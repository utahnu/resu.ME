"""Autoscraper. Reads sources.json, collects events, saves them via db.add_event.

Run:   python scraper.py            (all sources)
       python scraper.py byu-cal    (one source by name)
Schedule daily with cron:  0 6 * * * cd /path/to/app && python scraper.py
"""
import json
import re
import sys
import time
from datetime import date, datetime
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar

import db

UA = "resuME-bot/0.1 (student project; contact: you@example.com)"  # <- put a real contact
DELAY = 1.5  # seconds between requests, be polite

TYPE_KEYWORDS = {
    "Career fairs": ["career fair", "job fair", "expo", "recruit"],
    "Hackathons": ["hackathon", "codefest", "datathon"],
    "Networking mixers": ["networking", "mixer", "alumni"],
    "Workshops": ["workshop", "resume", "bootcamp", "training"],
    "Guest speakers": ["speaker", "panel", "fireside", "keynote", "talk"],
    "Info sessions": ["info session", "information session", "employer"],
    "Volunteering": ["volunteer", "service project", "community service"],
}

_robots = {}


def allowed(url):
    host = "{0.scheme}://{0.netloc}".format(urlparse(url))
    if host not in _robots:
        rp = RobotFileParser(host + "/robots.txt")
        try:
            rp.read()
        except Exception:
            rp = None  # robots.txt unreachable -> treat as allowed
        _robots[host] = rp
    rp = _robots[host]
    return True if rp is None else rp.can_fetch(UA, url)


def fetch(url):
    if not allowed(url):
        raise PermissionError("blocked by robots.txt")
    r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
    r.raise_for_status()
    return r.text


# ------------------------------------------------------------------ parsers
def parse_ical(text):
    """Yield raw event dicts from an .ics feed. (Recurring RRULE events: first occurrence only.)"""
    cal = Calendar.from_ical(text)
    for c in cal.walk("VEVENT"):
        start = c.get("dtstart")
        if not start:
            continue
        s = start.dt
        s = s.date() if isinstance(s, datetime) else s
        yield {
            "title": str(c.get("summary", "")),
            "start": s.isoformat(),
            "place": str(c.get("location", "")),
            "description": str(c.get("description", "")),
            "url": str(c.get("url", "")),
        }


def _walk_jsonld(node):
    if isinstance(node, list):
        for n in node:
            yield from _walk_jsonld(n)
    elif isinstance(node, dict):
        if "@graph" in node:
            yield from _walk_jsonld(node["@graph"])
        types = node.get("@type", [])
        types = [types] if isinstance(types, str) else types
        if any(t.endswith("Event") for t in types):
            yield node


def _place_text(loc):
    if isinstance(loc, list):
        loc = loc[0] if loc else {}
    if isinstance(loc, str):
        return loc
    if not isinstance(loc, dict):
        return ""
    addr = loc.get("address", "")
    if isinstance(addr, dict):
        addr = ", ".join(addr.get(k, "") for k in ("streetAddress", "addressLocality", "addressRegion") if addr.get(k))
    return ", ".join(p for p in (loc.get("name", ""), addr) if p)


def parse_jsonld(html):
    """Yield raw event dicts from schema.org Event markup in any web page."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        for ev in _walk_jsonld(data):
            if not ev.get("startDate"):
                continue
            mode = str(ev.get("eventAttendanceMode", ""))
            yield {
                "title": ev.get("name", ""),
                "start": str(ev["startDate"])[:10],
                "place": _place_text(ev.get("location")),
                "description": re.sub(r"<[^>]+>", " ", str(ev.get("description", ""))),
                "url": ev.get("url", ""),
                "virtual": "Online" in mode and "Mixed" not in mode,
            }


PARSERS = {"ical": parse_ical, "jsonld": parse_jsonld}


# ------------------------------------------------------------ normalization
def guess_type(text):
    text = text.lower()
    for etype, words in TYPE_KEYWORDS.items():
        if any(w in text for w in words):
            return etype
    return "Other"


def normalize(raw, src):
    text = f"{raw['title']} {raw['description']}"
    place = raw.get("place", "").strip()
    virtual = raw.get("virtual") or (not place and bool(re.search(r"online|zoom|virtual|webinar", text, re.I)))
    return {
        "title": raw["title"].strip(),
        "start": raw["start"],
        "type": src.get("default_type") or guess_type(text),
        "place": place or (src.get("default_place") or ""),
        "description": " ".join(raw["description"].split())[:400],
        "url": raw.get("url", ""),
        "virtual": virtual,
        "source": src["name"],
        "school": src.get("school"),
        "majors": ",".join(src.get("majors", [])),
        # Set lat/lng in sources.json if every event is at one venue (skips geocoding)
        "lat": src.get("lat"),
        "lng": src.get("lng"),
    }


# --------------------------------------------------------------------- main
def run(only=None, path="sources.json"):
    with open(path) as f:
        sources = json.load(f)
    today = date.today().isoformat()

    for src in sources:
        if only and src["name"] != only:
            continue
        added = dup = skipped = 0
        try:
            body = fetch(src["url"])
            for raw in PARSERS[src["kind"]](body):
                if not raw["title"] or raw["start"] < today:
                    skipped += 1
                    continue
                result = db.add_event(normalize(raw, src), status="approved")
                added += result == "added"
                dup += result == "duplicate"
                time.sleep(0.2)  # geocoding is rate-limited; cached after first lookup
        except Exception as e:  # one broken source must not stop the rest
            print(f"[{src['name']}] FAILED: {e}")
            continue
        print(f"[{src['name']}] added={added} duplicate={dup} skipped={skipped}")
        time.sleep(DELAY)


if __name__ == "__main__":
    run(only=sys.argv[1] if len(sys.argv) > 1 else None)
