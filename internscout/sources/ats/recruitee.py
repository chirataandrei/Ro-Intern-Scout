from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    status, data = http.get_json(f"https://{token}.recruitee.com/api/offers/")
    if status != 200 or not isinstance(data, dict):
        return []
    jobs: list[Job] = []
    for raw in data.get("offers") or []:
        locs = [str(raw.get("city") or "")]
        for loc in raw.get("locations") or []:
            if isinstance(loc, dict):
                locs.extend(
                    [
                        str(loc.get("name") or ""),
                        str(loc.get("city") or ""),
                        str(loc.get("country") or ""),
                    ]
                )
        job_id = str(raw.get("id") or raw.get("guid") or "")
        jobs.append(
            Job(
                uid=uid("recruitee", token, job_id),
                company=company.name,
                category=company.category,
                title=str(raw.get("title") or "").strip(),
                location=", ".join(x for x in locs if x),
                url=str(raw.get("careers_url") or raw.get("careers_apply_url") or ""),
                source="recruitee",
                published=str(raw.get("published_at") or ""),
            )
        )
    return jobs
