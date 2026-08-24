from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid


def _loc(raw: dict) -> str:
    loc = raw.get("workLocation") or raw.get("location") or ""
    if isinstance(loc, dict):
        return str(loc.get("label") or loc.get("name") or loc.get("city") or "")
    return str(loc or "")


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    if not token:
        return []
    jobs: list[Job] = []
    seen: set[str] = set()
    for url in (
        f"https://api.rippling.com/platform/api/ats/v1/board/{token}/jobs",
        f"https://ats.rippling.com/api/v2/board/{token}/jobs?page=0&pageSize=50",
    ):
        status, data = http.get_json(url)
        items = data
        if isinstance(data, dict):
            items = data.get("items") or data.get("jobs") or data.get("data") or []
        if status != 200 or not isinstance(items, list):
            continue
        for raw in items:
            if not isinstance(raw, dict):
                continue
            job_id = str(raw.get("uuid") or raw.get("id") or "")
            if not job_id or job_id in seen:
                continue
            seen.add(job_id)
            jobs.append(
                Job(
                    uid=uid("rippling", token, job_id),
                    company=company.name,
                    category=company.category,
                    title=str(raw.get("name") or raw.get("title") or "").strip(),
                    location=_loc(raw),
                    url=str(raw.get("url") or f"https://ats.rippling.com/{token}/jobs/{job_id}"),
                    source="rippling",
                    published=str(raw.get("createdOn") or raw.get("publishedAt") or ""),
                )
            )
        if jobs:
            return jobs
    return jobs
