from __future__ import annotations

from internscout.filters import is_student_entry, is_tech_role
from internscout.http import HttpClient
from internscout.models import Job
from internscout.sources import uid

LIST_URL = "https://jobicy.com/api/v2/remote-jobs?count=200&geo=europe"


def fetch_jobs(http: HttpClient) -> list[Job]:
    status, data = http.get_json(LIST_URL)
    if status != 200 or not isinstance(data, dict):
        return []
    jobs: list[Job] = []
    for raw in data.get("jobs") or []:
        if not isinstance(raw, dict):
            continue
        title = str(raw.get("jobTitle") or "").strip()
        if not title or not is_student_entry(title) or not is_tech_role(title):
            continue
        job_id = str(raw.get("id") or "").strip()
        url = str(raw.get("url") or "").strip()
        if not job_id or not url:
            continue
        company = str(raw.get("companyName") or "").strip()
        geo = str(raw.get("jobGeo") or "").strip()
        location = f"Remote - {geo}" if geo and geo.lower() != "anywhere" else "Remote - Europe"
        jobs.append(
            Job(
                uid=uid("jobicy", "jobicy", job_id),
                company=company or "Unknown company",
                category="aggregator",
                title=title,
                location=location,
                url=url,
                source="jobicy",
                published=str(raw.get("pubDate") or ""),
            )
        )
    return jobs
