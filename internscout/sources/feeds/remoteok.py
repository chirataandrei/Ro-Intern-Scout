from __future__ import annotations

from internscout.filters import is_america, is_student_entry, is_tech_role
from internscout.http import HttpClient
from internscout.models import Job
from internscout.sources import uid

LIST_URL = "https://remoteok.com/api"


def fetch_jobs(http: HttpClient) -> list[Job]:
    status, data = http.get_json(LIST_URL, headers={"Accept": "application/json"})
    if status != 200 or not isinstance(data, list):
        return []
    jobs: list[Job] = []
    for raw in data:
        # The first row is a legal notice, not a job: it has no "id".
        if not isinstance(raw, dict) or not raw.get("id"):
            continue
        title = str(raw.get("position") or "").strip()
        if not title or not is_student_entry(title) or not is_tech_role(title):
            continue
        location = str(raw.get("location") or "").strip()
        if is_america(location):
            continue
        job_id = str(raw.get("id"))
        company = str(raw.get("company") or "").strip()
        url = str(raw.get("url") or raw.get("apply_url") or "").strip()
        if url and not url.startswith("http"):
            url = f"https://remoteok.com{url}"
        if not url:
            continue
        jobs.append(
            Job(
                uid=uid("remoteok", "remoteok", job_id),
                company=company or "Unknown company",
                category="aggregator",
                title=title,
                location=f"Remote - {location}".strip(" -") if location else "Remote",
                url=url,
                source="remoteok",
                published=str(raw.get("date") or ""),
            )
        )
    return jobs
