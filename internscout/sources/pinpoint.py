from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    jobs: list[Job] = []
    for url in (
        f"https://{token}.pinpointhq.com/postings.json",
        f"https://{token}.pinpointhq.com/jobs.json",
    ):
        status, data = http.get_json(url)
        items = data
        if isinstance(data, dict):
            items = data.get("data") or data.get("jobs") or data.get("postings") or []
        if status != 200 or not isinstance(items, list):
            continue
        for raw in items:
            if not isinstance(raw, dict):
                continue
            attrs = raw.get("attributes") if isinstance(raw.get("attributes"), dict) else raw
            loc = attrs.get("location") or attrs.get("workplace") or ""
            if isinstance(loc, dict):
                loc = ", ".join(str(x) for x in loc.values() if x)
            job_id = str(raw.get("id") or attrs.get("slug") or attrs.get("id") or "")
            jobs.append(
                Job(
                    uid=uid("pinpoint", token, job_id),
                    company=company.name,
                    category=company.category,
                    title=str(attrs.get("title") or attrs.get("name") or "").strip(),
                    location=str(loc),
                    url=str(
                        attrs.get("url")
                        or raw.get("url")
                        or f"https://{token}.pinpointhq.com/postings/{job_id}"
                    ),
                    source="pinpoint",
                )
            )
        if jobs:
            return jobs
    return jobs
