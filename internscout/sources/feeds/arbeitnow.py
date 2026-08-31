from __future__ import annotations

from internscout.filters import is_student_entry, is_tech_role
from internscout.http import HttpClient
from internscout.models import Job
from internscout.sources import uid

LIST_URL = "https://arbeitnow.com/api/job-board-api"


def fetch_jobs(http: HttpClient) -> list[Job]:
    status, data = http.get_json(LIST_URL)
    if status != 200 or not isinstance(data, dict):
        return []
    jobs: list[Job] = []
    for raw in data.get("data") or []:
        if not isinstance(raw, dict):
            continue
        title = str(raw.get("title") or "").strip()
        if not title or not is_student_entry(title) or not is_tech_role(title):
            continue
        job_id = str(raw.get("slug") or "").strip()
        url = str(raw.get("url") or "").strip()
        if not job_id or not url:
            continue
        company = str(raw.get("company_name") or "").strip()
        location = str(raw.get("location") or "").strip()
        if raw.get("remote"):
            location = f"Remote - {location}".strip(" -")
        jobs.append(
            Job(
                uid=uid("arbeitnow", "arbeitnow", job_id),
                company=company or "Unknown company",
                category="aggregator",
                title=title,
                location=location or "Europe",
                url=url,
                source="arbeitnow",
                published=str(raw.get("created_at") or ""),
            )
        )
    return jobs
