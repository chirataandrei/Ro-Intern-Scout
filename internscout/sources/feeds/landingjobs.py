from __future__ import annotations

import re

from internscout.filters import is_student_entry, is_tech_role
from internscout.http import HttpClient
from internscout.models import Job
from internscout.sources import uid

LIST_URL = "https://landing.jobs/api/v1/jobs"
SLUG_RE = re.compile(r"landing\.jobs/at/([^/]+)/")


def company_from_url(url: str) -> str:
    m = SLUG_RE.search(url)
    if not m:
        return ""
    return " ".join(part.capitalize() for part in m.group(1).split("-"))


def fetch_jobs(http: HttpClient) -> list[Job]:
    status, data = http.get_json(LIST_URL)
    if status != 200 or not isinstance(data, list):
        return []
    jobs: list[Job] = []
    for raw in data:
        if not isinstance(raw, dict):
            continue
        title = str(raw.get("title") or "").strip()
        if not title or not is_student_entry(title) or not is_tech_role(title):
            continue
        url = str(raw.get("url") or "").strip()
        job_id = str(raw.get("id") or "").strip()
        if not url or not job_id:
            continue
        company = company_from_url(url)
        places = [
            f"{p.get('city', '')}".strip()
            for p in (raw.get("locations") or [])
            if isinstance(p, dict) and p.get("city")
        ]
        location = ", ".join(places) or "Europe"
        if raw.get("remote"):
            location = f"Remote - {location}"
        jobs.append(
            Job(
                uid=uid("landingjobs", "landingjobs", job_id),
                company=company or "Unknown company",
                category="aggregator",
                title=title,
                location=location,
                url=url,
                source="landingjobs",
                published=str(raw.get("published_at") or ""),
            )
        )
    return jobs
