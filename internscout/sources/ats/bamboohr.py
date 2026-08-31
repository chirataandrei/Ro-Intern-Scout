from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    status, data = http.get_json(f"https://{token}.bamboohr.com/careers/list")
    items = data
    if isinstance(data, dict):
        items = data.get("result") or data.get("jobs") or data.get("meta") or []
        if isinstance(items, dict):
            items = items.get("jobs") or []
    if status != 200 or not isinstance(items, list):
        return []
    jobs: list[Job] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        job_id = str(raw.get("id") or raw.get("jobOpeningId") or raw.get("atsJobId") or "")
        loc = raw.get("location") or raw.get("atsLocation") or {}
        if isinstance(loc, dict):
            location = ", ".join(
                str(x)
                for x in (loc.get("city"), loc.get("state"), loc.get("country"), loc.get("name"))
                if x
            )
        else:
            location = str(loc or "")
        jobs.append(
            Job(
                uid=uid("bamboohr", token, job_id),
                company=company.name,
                category=company.category,
                title=str(raw.get("jobOpeningName") or raw.get("title") or "").strip(),
                location=location,
                url=str(
                    raw.get("jobOpeningShareUrl")
                    or f"https://{token}.bamboohr.com/careers/{job_id}"
                ),
                source="bamboohr",
            )
        )
    return jobs
