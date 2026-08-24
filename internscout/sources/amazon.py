from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid

QUERIES = [
    "https://www.amazon.jobs/en/search.json?base_query=intern&loc_query=Romania&result_limit=100",
    "https://www.amazon.jobs/en/search.json?base_query=intern&loc_query=Bucharest&result_limit=100",
    "https://www.amazon.jobs/en/search.json?base_query=intern&loc_query=Iasi&result_limit=100",
    "https://www.amazon.jobs/en/search.json?base_query=internship&country=ROM&result_limit=100",
]


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    for url in QUERIES:
        status, data = http.get_json(url)
        if status != 200 or not isinstance(data, dict):
            continue
        for raw in data.get("jobs") or []:
            job_id = str(raw.get("id_icims") or raw.get("id") or "")
            if not job_id or job_id in seen:
                continue
            seen.add(job_id)
            loc_bits = [
                str(raw.get("normalized_location") or ""),
                str(raw.get("location") or ""),
                str(raw.get("city") or ""),
                str(raw.get("country_code") or ""),
                " ".join(str(x) for x in (raw.get("locations") or []) if x),
            ]
            path = str(raw.get("job_path") or "")
            jobs.append(
                Job(
                    uid=uid("amazon", "amazon", job_id),
                    company=company.name,
                    category=company.category,
                    title=str(raw.get("title") or "").strip(),
                    location=" ".join(x for x in loc_bits if x),
                    url=f"https://www.amazon.jobs{path}" if path.startswith("/") else path,
                    source="amazon",
                    published=str(raw.get("posted_date") or ""),
                )
            )
    return jobs
