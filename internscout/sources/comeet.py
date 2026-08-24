from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    uid_key = str(company.extra.get("uid") or token)
    url = f"https://www.comeet.co/careers-api/2.0/company/{uid_key}/positions?details=true"
    api_token = str(company.extra.get("api_token") or "")
    if api_token:
        url += f"&token={api_token}"
    status, data = http.get_json(url)
    items = data
    if isinstance(data, dict):
        items = data.get("positions") or data.get("data") or data.get("required") or []
    if status != 200 or not isinstance(items, list):
        return []
    jobs: list[Job] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        loc = raw.get("location") or {}
        if isinstance(loc, dict):
            location = ", ".join(
                str(x)
                for x in (loc.get("city"), loc.get("state"), loc.get("country"), loc.get("name"))
                if x
            )
        else:
            location = str(loc or "")
        job_id = str(raw.get("uid") or raw.get("id") or "")
        jobs.append(
            Job(
                uid=uid("comeet", token, job_id),
                company=company.name,
                category=company.category,
                title=str(raw.get("name") or raw.get("title") or "").strip(),
                location=location,
                url=str(raw.get("url_comeet_hosted_page") or raw.get("url_active_page") or ""),
                source="comeet",
            )
        )
    return jobs
