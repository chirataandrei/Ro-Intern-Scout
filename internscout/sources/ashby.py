from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    status, data = http.get_json(f"https://api.ashbyhq.com/posting-api/job-board/{token}")
    if status != 200 or not isinstance(data, dict):
        return []
    jobs: list[Job] = []
    for raw in data.get("jobs") or []:
        locs = [str(raw.get("location") or "")]
        for extra in raw.get("secondaryLocations") or []:
            if isinstance(extra, dict):
                locs.append(str(extra.get("location") or ""))
            else:
                locs.append(str(extra))
        job_id = str(raw.get("id") or "")
        jobs.append(
            Job(
                uid=uid("ashby", token, job_id),
                company=company.name,
                category=company.category,
                title=str(raw.get("title") or "").strip(),
                location=", ".join(x for x in locs if x),
                url=str(raw.get("jobUrl") or raw.get("applyUrl") or ""),
                source="ashby",
                published=str(raw.get("publishedAt") or ""),
            )
        )
    return jobs
