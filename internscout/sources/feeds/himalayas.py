from __future__ import annotations

from urllib.parse import quote

from internscout.filters import is_student_entry, is_tech_role
from internscout.http import HttpClient
from internscout.models import Job
from internscout.sources import uid

LIST_URL = "https://himalayas.app/jobs/api"
MAX_PAGES = 5  # the API caps each page at 20 rows regardless of ?limit=


def fetch_jobs(http: HttpClient) -> list[Job]:
    jobs: list[Job] = []
    cursor: str | None = None
    for _ in range(MAX_PAGES):
        url = f"{LIST_URL}?cursor={quote(cursor)}" if cursor else LIST_URL
        status, data = http.get_json(url)
        if status != 200 or not isinstance(data, dict):
            break
        rows = data.get("jobs") or []
        if not rows:
            break
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            title = str(raw.get("title") or "").strip()
            if not title or not is_student_entry(title) or not is_tech_role(title):
                continue
            job_id = str(raw.get("guid") or "").strip()
            url_apply = str(raw.get("applicationLink") or "").strip()
            if not job_id or not url_apply:
                continue
            company = str(raw.get("companyName") or "").strip()
            restrictions = [str(r) for r in (raw.get("locationRestrictions") or []) if r]
            location = f"Remote - {', '.join(restrictions)}" if restrictions else "Remote"
            jobs.append(
                Job(
                    uid=uid("himalayas", "himalayas", job_id),
                    company=company or "Unknown company",
                    category="aggregator",
                    title=title,
                    location=location,
                    url=url_apply,
                    source="himalayas",
                    published=str(raw.get("pubDate") or ""),
                )
            )
        cursor = data.get("nextCursor")
        if not cursor:
            break
    return jobs
