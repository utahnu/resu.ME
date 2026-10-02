import requests

import time, csv

ADZUNA_ID = "8464c5d4"
ADZUNA_KEY = "bcc892bcff1b1fc3cf2a427e079c98fd"

class Job_Fetcher():
    def __init__(self, location = "Provo, UT", radius = 25):
        self.location = location
        self.radius = radius
        
    def fetch_jobs(self, searchpages = 1, search_term = ""):
        jobs = []
        for page in range(1, searchpages + 1):
            r = requests.get(
            f"https://api.adzuna.com/v1/api/jobs/us/search/{page}",
            params={
                "app_id": ADZUNA_ID, "app_key": ADZUNA_KEY,
                "where": self.location, "distance": self.radius,
                "what": search_term, "results_per_page": 50,
                "content-type": "application/json",
            },)
            r.raise_for_status() # checks if the request worked
            for j in r.json().get("results"):
                jobs.append({
                    "id": str(j["id"]),
                    "title": j.get("title", " "),
                    "company": (j.get("company") or {}).get("display_name", ""),
                    "location": (j.get("location") or {}).get("display_name", ""),
                    "url": (j.get("redirect_url", ""))
            })
            time.sleep(1)
            
        self.jobs = jobs
        return jobs

    def get_filtered_jobs(self):
        jobs_filtered = []
        for j in self.jobs:
            if False:
                continue # doesnt do any filtering
            
            jobs_filtered.append(j)
        
        return jobs_filtered
            
    
if __name__ == "__main__": # Gets a bunch of jobs for Provo Utah
    jf = Job_Fetcher()
    print("Finding jobs...")
    print(jf.fetch_jobs())