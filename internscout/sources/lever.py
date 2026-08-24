from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    status, data = http.get_json(f"https://api.lever.co/v0/postings/{token}?mode=json")
    if status != 200 or not isinstance(data, list):
        return []
    jobs: list[Job] = []
    for raw in data:
        cats = raw.get("categories") or {}
        locs = []
        if isinstance(cats, dict):
            if cats.get("location"):
                locs.append(str(cats["location"]))
            locs.extend(str(x) for x in (cats.get("allLocations") or []) if x)
        job_id = str(raw.get("id") or "")
        jobs.append(
            Job(
                uid=uid("lever", token, job_id),
                company=company.name,
                category=company.category,
                title=str(raw.get("text") or raw.get("title") or "").strip(),
                location=", ".join(locs),
                url=str(raw.get("hostedUrl") or raw.get("applyUrl") or ""),
                source="lever",
                published=str(raw.get("createdAt") or ""),
            )
        )
    return jobs
