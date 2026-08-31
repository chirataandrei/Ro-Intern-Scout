from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    status, data = http.get_json(f"https://{token}.breezy.hr/json")
    if status != 200 or not isinstance(data, list):
        return []
    jobs: list[Job] = []
    for raw in data:
        if not isinstance(raw, dict):
            continue
        loc = raw.get("location") or {}
        if isinstance(loc, dict):
            location = ", ".join(
                str(x)
                for x in (loc.get("city"), loc.get("region"), loc.get("country"), loc.get("name"))
                if x
            )
        else:
            location = str(loc or "")
        job_id = str(raw.get("_id") or raw.get("id") or raw.get("friendly_id") or "")
        jobs.append(
            Job(
                uid=uid("breezy", token, job_id),
                company=company.name,
                category=company.category,
                title=str(raw.get("name") or raw.get("title") or "").strip(),
                location=location,
                url=str(raw.get("url") or raw.get("application_url") or ""),
                source="breezy",
                published=str(raw.get("published_date") or raw.get("created_at") or ""),
            )
        )
    return jobs
