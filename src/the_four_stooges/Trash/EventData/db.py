"""Storage + search. Everything (scraper, submit form, app) goes through here."""
import hashlib
import math
import os
import sqlite3
from datetime import date

DB_PATH = os.environ.get("RESUME_DB", "events.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT,
    start TEXT NOT NULL,            -- ISO date, e.g. 2026-11-04
    place TEXT,
    description TEXT,
    url TEXT,
    source TEXT,                    -- source name from sources.json, or 'user'
    school TEXT,
    lat REAL,
    lng REAL,
    virtual INTEGER DEFAULT 0,
    majors TEXT DEFAULT '',         -- comma-separated tags, '' = all majors
    status TEXT DEFAULT 'approved', -- approved | pending | rejected
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS geocache (
    query TEXT PRIMARY KEY, lat REAL, lng REAL
);
"""


def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def make_id(title, start, place):
    key = f"{title.strip().lower()}|{start}|{(place or '').strip().lower()}"
    return hashlib.sha1(key.encode()).hexdigest()[:16]


# ---------------------------------------------------------------- geocoding
def geocode(query):
    """Return (lat, lng) or (None, None). Cached in SQLite (Nominatim allows ~1 req/sec)."""
    query = (query or "").strip()
    if not query:
        return None, None
    with connect() as con:
        row = con.execute("SELECT lat, lng FROM geocache WHERE query=?", (query,)).fetchone()
        if row:
            return row["lat"], row["lng"]
    try:
        from geopy.geocoders import Nominatim

        hit = Nominatim(user_agent="resuME-app").geocode(query, timeout=10)
    except Exception:
        return None, None
    if not hit:
        return None, None
    with connect() as con:
        con.execute("INSERT OR REPLACE INTO geocache VALUES (?,?,?)", (query, hit.latitude, hit.longitude))
    return hit.latitude, hit.longitude


def haversine_mi(lat1, lng1, lat2, lng2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(a))


# ------------------------------------------------------------------ writing
def add_event(ev, status="approved"):
    """Insert an event dict. Returns 'added' or 'duplicate'.

    Required keys: title, start (YYYY-MM-DD).
    Optional: type, place, description, url, source, school, lat, lng, virtual, majors.
    """
    title = (ev.get("title") or "").strip()
    start = (ev.get("start") or "").strip()[:10]
    if not title or not start:
        raise ValueError("title and start date are required")

    virtual = 1 if ev.get("virtual") else 0
    lat, lng = ev.get("lat"), ev.get("lng")
    if not virtual and lat is None and ev.get("place"):
        lat, lng = geocode(ev["place"])

    eid = make_id(title, start, ev.get("place"))
    with connect() as con:
        exists = con.execute("SELECT 1 FROM events WHERE id=?", (eid,)).fetchone()
        if exists:
            # refresh details, but never touch status (keeps moderation decisions)
            con.execute(
                "UPDATE events SET description=?, url=? WHERE id=?",
                (ev.get("description"), ev.get("url"), eid),
            )
            return "duplicate"
        con.execute(
            "INSERT INTO events (id,title,type,start,place,description,url,source,school,lat,lng,virtual,majors,status)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (eid, title, ev.get("type"), start, ev.get("place"), ev.get("description"), ev.get("url"),
             ev.get("source"), ev.get("school"), lat, lng, virtual, ev.get("majors", ""), status),
        )
    return "added"


def pending_events():
    with connect() as con:
        return con.execute("SELECT * FROM events WHERE status='pending' ORDER BY created_at").fetchall()


def set_status(event_id, status):
    with connect() as con:
        con.execute("UPDATE events SET status=? WHERE id=?", (status, event_id))


# ------------------------------------------------------------------ reading
def find_events(profile):
    """Drop-in replacement for the sample find_events in app.py. Same output keys."""
    radius = profile.get("radius")
    if radius is not None and profile.get("radius_unit") == "km":
        radius = radius / 1.609

    ulat, ulng = geocode(profile.get("location"))
    types = profile.get("event_types") or []

    with connect() as con:
        rows = con.execute(
            "SELECT * FROM events WHERE status='approved' AND start >= ? ORDER BY start",
            (date.today().isoformat(),),
        ).fetchall()

    results = []
    for r in rows:
        virtual = bool(r["virtual"])
        dist = None
        if not virtual and ulat is not None and r["lat"] is not None:
            dist = haversine_mi(ulat, ulng, r["lat"], r["lng"])

        if virtual and not profile.get("include_virtual", True):
            continue
        # Radius filter. If we couldn't geocode the user, skip it rather than hide everything.
        if not virtual and radius is not None and ulat is not None:
            if dist is None or dist > radius:  # events with unknown location are excluded
                continue
        if types and r["type"] not in types:
            continue

        d = date.fromisoformat(r["start"][:10])
        results.append({
            "title": r["title"],
            "type": r["type"] or "Other",
            "date": f"{d:%b} {d.day}",
            "place": "Online" if virtual else (r["place"] or "TBA"),
            "distance_mi": round(dist) if dist is not None else 0,
            "virtual": virtual,
            "description": r["description"] or "",
            "url": r["url"],
        })
    return results
