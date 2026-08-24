from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    jobs: list[Job] = []
    offset = 0
    limit = 100
    while True:
        status, data = http.get_json(
            f"https://api.smartrecruiters.com/v1/companies/{token}/postings"
            f"?limit={limit}&offset={offset}&country=ro"
        )
        if status != 200 or not isinstance(data, dict):
            break
        batch = data.get("content") or []
        for raw in batch:
            loc = raw.get("location") or {}
            parts = []
            if isinstance(loc, dict):
                parts = [
                    str(loc.get("city") or ""),
                    str(loc.get("region") or ""),
                    str(loc.get("country") or ""),
                    str(loc.get("fullLocation") or ""),
                ]
            elif isinstance(loc, str):
                parts = [loc]
            job_id = str(raw.get("id") or "")
            jobs.append(
                Job(
                    uid=uid("smartrecruiters", token, job_id),
                    company=company.name,
                    category=company.category,
                    title=str(raw.get("name") or raw.get("title") or "").strip(),
                    location=", ".join(p for p in parts if p),
                    url=f"https://jobs.smartrecruiters.com/{token}/{job_id}",
                    source="smartrecruiters",
                    published=str(raw.get("releasedDate") or ""),
                )
            )
        total = int(data.get("totalFound") or 0)
        offset += len(batch)
        if not batch or offset >= total or offset >= 400:
            break
    return jobs
