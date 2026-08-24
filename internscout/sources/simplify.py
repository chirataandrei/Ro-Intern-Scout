from __future__ import annotations

from internscout.filters import is_romania, is_spring_week, is_student_entry
from internscout.http import HttpClient
from internscout.models import Job
from internscout.sources import uid

LISTING_URLS = [
    "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/.github/scripts/listings.json",
    "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/.github/scripts/listings.json",
]

QUANT_TITLE_RE = (
    "quant",
    "trader",
    "trading intern",
    "technologist",
    "software",
    "engineer",
    "developer",
    "research intern",
    "researcher – intern",
    "researcher - intern",
    "swe",
    "sde",
)


def _is_quant_student(title: str) -> bool:
    t = title.lower()
    if "trading card" in t or "collectible" in t:
        return False
    if is_spring_week(title):
        return True
    if not is_student_entry(title):
        return False
    return any(k in t for k in QUANT_TITLE_RE)


def fetch_jobs(http: HttpClient) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    for url in LISTING_URLS:
        status, data = http.get_json(url)
        if status != 200 or not isinstance(data, list):
            continue
        for raw in data:
            if not isinstance(raw, dict):
                continue
            if not raw.get("active") or raw.get("is_visible") is False:
                continue
            job_id = str(raw.get("id") or "")
            if not job_id or job_id in seen:
                continue
            title = str(raw.get("title") or "").strip()
            company = str(raw.get("company_name") or "").strip()
            locs = [str(x) for x in (raw.get("locations") or []) if x]
            location = ", ".join(locs)
            category = str(raw.get("category") or "")
            quant = "quant" in category.lower()
            extra = f"{company} {location} {raw.get('url') or ''}"
            if quant and not _is_quant_student(title):
                continue
            if not quant and not is_student_entry(title, extra):
                continue
            if not quant and not is_romania(location):
                continue
            seen.add(job_id)
            jobs.append(
                Job(
                    uid=uid("simplify", "simplify", job_id),
                    company=company or "Simplify",
                    category="quant" if quant else "aggregator",
                    title=title,
                    location=location,
                    url=str(raw.get("url") or ""),
                    source="simplify",
                )
            )
    return jobs
