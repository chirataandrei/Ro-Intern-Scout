from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    host = company.host or f"{token}.eightfold.ai"
    domain = str(company.extra.get("domain") or f"{token}.com")
    query = "intern OR internship OR trainee OR stagiu"
    url = (
        f"https://{host}/api/apply/v2/jobs"
        f"?domain={domain}&query={query}&location=Romania&start=0&num=40"
    )
    status, data = http.get_json(url)
    if status != 200 or not isinstance(data, dict):
        return []
    jobs: list[Job] = []
    for raw in data.get("positions") or data.get("data") or data.get("jobs") or []:
        if not isinstance(raw, dict):
            continue
        locs = raw.get("locations") or raw.get("location") or ""
        if isinstance(locs, list):
            bits = []
            for loc in locs:
                if isinstance(loc, dict):
                    bits.append(str(loc.get("name") or loc.get("city") or ""))
                else:
                    bits.append(str(loc))
            locs = ", ".join(x for x in bits if x)
        job_id = str(raw.get("id") or raw.get("jobId") or raw.get("atsJobId") or "")
        path = str(raw.get("canonicalPositionUrl") or raw.get("url") or "")
        if path and not path.startswith("http"):
            path = f"https://{host}{path}"
        jobs.append(
            Job(
                uid=uid("eightfold", token, job_id),
                company=company.name,
                category=company.category,
                title=str(raw.get("name") or raw.get("title") or "").strip(),
                location=str(locs),
                url=path or f"https://{host}/careers/job/{job_id}",
                source="eightfold",
            )
        )
    return jobs
