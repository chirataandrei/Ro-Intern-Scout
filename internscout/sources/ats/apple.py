from __future__ import annotations

import json

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid

SEARCH_BODY = {
    "query": "intern Romania OR Bucharest OR intern",
    "filters": {
        "locations": [{"field": "countryCode", "value": "ROU"}],
    },
    "page": 1,
    "locale": "en-us",
}


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    status, data = http.post_json(
        "https://jobs.apple.com/api/v1/search",
        SEARCH_BODY,
        extra_headers={"Referer": "https://jobs.apple.com/en-us/search"},
    )
    if status != 200 or not isinstance(data, dict):
        return []
    res = data.get("res") or data.get("searchResults") or data
    items = []
    if isinstance(res, dict):
        items = res.get("searchResults") or res.get("jobs") or []
    elif isinstance(res, list):
        items = res
    jobs: list[Job] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        loc = raw.get("locations") or raw.get("location") or ""
        if isinstance(loc, list):
            loc = ", ".join(json.dumps(x) if isinstance(x, dict) else str(x) for x in loc)
        job_id = str(raw.get("positionId") or raw.get("id") or "")
        title = str(raw.get("postingTitle") or raw.get("title") or "").strip()
        jobs.append(
            Job(
                uid=uid("apple", "apple", job_id or title),
                company=company.name,
                category=company.category,
                title=title,
                location=str(loc),
                url=str(
                    raw.get("url")
                    or f"https://jobs.apple.com/en-us/details/{job_id}"
                ),
                source="apple",
            )
        )
    return jobs
