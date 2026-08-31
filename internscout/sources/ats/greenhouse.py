from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    status, data = http.get_json(
        f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
    )
    if status != 200 or not isinstance(data, dict):
        return []
    jobs: list[Job] = []
    for raw in data.get("jobs") or []:
        loc = ""
        location = raw.get("location")
        if isinstance(location, dict):
            loc = str(location.get("name") or "")
        elif isinstance(location, str):
            loc = location
        offices = raw.get("offices") or []
        if isinstance(offices, list):
            loc = loc + " " + " ".join(
                str(o.get("name") or o.get("location") or "")
                for o in offices
                if isinstance(o, dict)
            )
        job_id = str(raw.get("id") or raw.get("absolute_url") or "")
        jobs.append(
            Job(
                uid=uid("greenhouse", token, job_id),
                company=company.name,
                category=company.category,
                title=str(raw.get("title") or "").strip(),
                location=loc.strip(),
                url=str(raw.get("absolute_url") or ""),
                source="greenhouse",
                published=str(raw.get("first_published") or raw.get("updated_at") or ""),
            )
        )
    return jobs
