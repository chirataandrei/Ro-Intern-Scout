from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    status, data = http.get_json(
        f"https://apply.workable.com/api/v1/widget/accounts/{token}?details=false"
    )
    if status != 200 or not isinstance(data, dict):
        return []
    jobs: list[Job] = []
    for raw in data.get("jobs") or []:
        parts = [str(raw.get("city") or ""), str(raw.get("state") or ""), str(raw.get("country") or "")]
        shortcode = str(raw.get("shortcode") or raw.get("id") or "")
        jobs.append(
            Job(
                uid=uid("workable", token, shortcode),
                company=company.name,
                category=company.category,
                title=str(raw.get("title") or "").strip(),
                location=", ".join(p for p in parts if p),
                url=str(
                    raw.get("url")
                    or raw.get("application_url")
                    or f"https://apply.workable.com/j/{shortcode}/"
                ),
                source="workable",
                published=str(raw.get("published_on") or ""),
            )
        )
    return jobs
