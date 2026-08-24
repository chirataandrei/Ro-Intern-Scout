from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    if not token:
        return []
    status, data = http.get_json(f"https://{token}.jobsoid.com/api/v1/jobs")
    items = data
    if isinstance(data, dict):
        items = data.get("jobs") or data.get("data") or data.get("items") or []
    if status != 200 or not isinstance(items, list):
        return []
    jobs: list[Job] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        job_id = str(raw.get("id") or raw.get("jobId") or raw.get("code") or "")
        loc = raw.get("location") or raw.get("city") or ""
        if isinstance(loc, dict):
            loc = ", ".join(str(x) for x in (loc.get("city"), loc.get("country"), loc.get("name")) if x)
        jobs.append(
            Job(
                uid=uid("jobsoid", token, job_id),
                company=company.name,
                category=company.category,
                title=str(raw.get("title") or raw.get("name") or "").strip(),
                location=str(loc),
                url=str(raw.get("url") or raw.get("jobUrl") or f"https://{token}.jobsoid.com/"),
                source="jobsoid",
            )
        )
    return jobs
