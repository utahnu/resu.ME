"""
Job -> Contacts pipeline
Stages: fetch jobs -> filter -> find company contacts -> write CSV

Setup:
    pip install requests pandas
    Free keys:  Adzuna  https://developer.adzuna.com/
                Hunter  https://hunter.io/api  (free tier ~25 searches/month)
    Set env vars: ADZUNA_ID, ADZUNA_KEY, HUNTER_KEY
"""
import os, csv, time, json
from urllib.parse import quote_plus
import requests

# ---------- CONFIG ----------
WHERE = "Provo, UT"          # city or ZIP
RADIUS_MILES = 25
SEARCH_TERM = ""             # optional broad term sent to Adzuna, e.g. "marketing"
PAGES = 2                    # 50 results per page
INCLUDE = []                 # keep job if ANY of these appear in title (empty = keep all)
EXCLUDE = ["intern", "driver"]  # drop job if ANY appear in title
MAX_COMPANIES = 15           # cap enrichment (Hunter free tier is small)
OUT_FILE = "jobs_with_contacts.csv"
SEEN_FILE = "seen_jobs.json"  # so reruns only show new postings

ADZUNA_ID = os.getenv("ADZUNA_ID")
ADZUNA_KEY = os.getenv("ADZUNA_KEY")
HUNTER_KEY = os.getenv("HUNTER_KEY")


# ---------- STAGE 1: FETCH ----------
def fetch_jobs():
    jobs = []
    for page in range(1, PAGES + 1):
        r = requests.get(
            f"https://api.adzuna.com/v1/api/jobs/us/search/{page}",
            params={
                "app_id": ADZUNA_ID, "app_key": ADZUNA_KEY,
                "where": WHERE, "distance": RADIUS_MILES,
                "what": SEARCH_TERM, "results_per_page": 50,
                "content-type": "application/json",
            },
            timeout=15,
        )
        r.raise_for_status()
        for j in r.json().get("results", []):
            jobs.append({
                "id": str(j["id"]),
                "title": j.get("title", ""),
                "company": (j.get("company") or {}).get("display_name", ""),
                "location": (j.get("location") or {}).get("display_name", ""),
                "url": j.get("redirect_url", ""),
            })
        time.sleep(1)
    return jobs


# ---------- STAGE 2: FILTER (edit this later) ----------
def filter_jobs(jobs):
    kept = []
    for j in jobs:
        t = j["title"].lower()
        if INCLUDE and not any(k.lower() in t for k in INCLUDE):
            continue
        if any(k.lower() in t for k in EXCLUDE):
            continue
        if not j["company"]:
            continue
        kept.append(j)
    return kept


# ---------- STAGE 3: ENRICH ----------
def find_contacts(company):
    """Ask Hunter for the company's domain and publicly listed people."""
    if not HUNTER_KEY:
        return None, []
    try:
        r = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={"company": company, "api_key": HUNTER_KEY, "limit": 10},
            timeout=15,
        )
        if r.status_code != 200:
            return None, []
        data = r.json().get("data", {})
    except requests.RequestException:
        return None, []

    people = []
    for e in data.get("emails", []):
        name = f"{e.get('first_name') or ''} {e.get('last_name') or ''}".strip()
        people.append({
            "name": name,
            "position": e.get("position") or "",
            "email": e.get("value"),
            "confidence": e.get("confidence"),
        })
    # surface likely hiring-relevant people first
    keywords = ("recruit", "talent", "hr", "human resources", "hiring", "director", "manager", "head")
    people.sort(key=lambda p: not any(k in p["position"].lower() for k in keywords))
    return data.get("domain"), people


def linkedin_search_link(company):
    return ("https://www.linkedin.com/search/results/people/?keywords="
            + quote_plus(f"{company} recruiter OR hiring manager"))


# ---------- STAGE 4: OUTPUT ----------
def load_seen():
    try:
        return set(json.load(open(SEEN_FILE)))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def main():
    if not (ADZUNA_ID and ADZUNA_KEY):
        raise SystemExit("Set ADZUNA_ID and ADZUNA_KEY environment variables.")

    seen = load_seen()
    jobs = [j for j in filter_jobs(fetch_jobs()) if j["id"] not in seen]
    print(f"{len(jobs)} new jobs after filtering")

    # look up each company once, not once per job
    contacts = {}
    for company in list(dict.fromkeys(j["company"] for j in jobs))[:MAX_COMPANIES]:
        contacts[company] = find_contacts(company)
        time.sleep(1)

    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["title", "company", "location", "job_url", "domain",
                    "contact_1", "contact_2", "contact_3", "linkedin_search"])
        for j in jobs:
            domain, people = contacts.get(j["company"], (None, []))
            cells = [f"{p['name']} | {p['position']} | {p['email']}" for p in people[:3]]
            cells += [""] * (3 - len(cells))
            w.writerow([j["title"], j["company"], j["location"], j["url"],
                        domain or "", *cells, linkedin_search_link(j["company"])])

    json.dump(sorted(seen | {j["id"] for j in jobs}), open(SEEN_FILE, "w"))
    print(f"Wrote {OUT_FILE}")


if __name__ == "__main__":
    main()