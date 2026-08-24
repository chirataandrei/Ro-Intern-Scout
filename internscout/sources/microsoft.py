from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid

SEARCH_URL = (
    "https://gcsservices.careers.microsoft.com/search/api/v1/search"
    "?l=en_us&pg=1&pgSz=50&o=Relevance&flt=true&ref=cms"
    "&searchPhrase=intern&loc=Romania"
)


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    jobs: list[Job] = []
    status, data = http.get_json(SEARCH_URL)
    if status != 200 or not isinstance(data, dict):
        status, data = http.post_json(
            "https://gcsservices.careers.microsoft.com/search/api/v1/search",
            {
                "searchText": "intern Romania",
                "filters": {"country": ["Romania"]},
                "pageSize": 50,
                "pageNumber": 1,
            },
        )
    if not isinstance(data, dict):
        return jobs
    operation = data.get("operationResult") or data
    result = operation.get("result") if isinstance(operation, dict) else data
    if not isinstance(result, dict):
        result = data
    items = result.get("jobs") or result.get("items") or []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        props = raw.get("properties") if isinstance(raw.get("properties"), dict) else {}
        loc = " ".join(
            [
                str(raw.get("location") or props.get("primaryLocation") or ""),
                str(props.get("locations") or ""),
                str(raw.get("country") or ""),
            ]
        )
        job_id = str(raw.get("jobId") or raw.get("jobIdOrSlug") or raw.get("id") or "")
        title = str(raw.get("title") or props.get("title") or "").strip()
        url = str(
            raw.get("url")
            or f"https://jobs.careers.microsoft.com/global/en/job/{job_id}"
        )
        jobs.append(
            Job(
                uid=uid("microsoft", "microsoft", job_id or title),
                company=company.name,
                category=company.category,
                title=title,
                location=loc,
                url=url,
                source="microsoft",
            )
        )
    return jobs
