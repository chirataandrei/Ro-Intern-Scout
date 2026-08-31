from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid

SEARCH_URL = (
    "https://www.metacareers.com/api/jobs/v1/search"
    "?q=intern&locations[0]=Bucharest%2C%20Romania"
    "&locations[1]=Romania"
)


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    jobs: list[Job] = []
    status, data = http.get_json(SEARCH_URL)
    if status != 200:
        status, data = http.post_json(
            "https://www.metacareers.com/graphql",
            {},
        )
        if status != 200:
            return jobs
    items = []
    if isinstance(data, dict):
        items = data.get("data") or data.get("job_search") or data.get("jobs") or []
        if isinstance(items, dict):
            items = items.get("jobs") or items.get("items") or []
    if not isinstance(items, list):
        return jobs
    for raw in items:
        if not isinstance(raw, dict):
            continue
        job_id = str(raw.get("id") or raw.get("job_id") or "")
        locs = raw.get("locations") or raw.get("location") or ""
        if isinstance(locs, list):
            locs = ", ".join(str(x) for x in locs)
        title = str(raw.get("title") or "").strip()
        jobs.append(
            Job(
                uid=uid("meta", "meta", job_id or title),
                company=company.name,
                category=company.category,
                title=title,
                location=str(locs),
                url=str(raw.get("url") or f"https://www.metacareers.com/jobs/{job_id}"),
                source="meta",
            )
        )
    return jobs
