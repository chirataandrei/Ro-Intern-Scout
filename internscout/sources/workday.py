from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid


def build_job_url(host: str, site: str, path: str) -> str:
    host = (host or "").strip().rstrip("/")
    site = (site or "").strip().strip("/")
    path = (path or "").strip()
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not path.startswith("/"):
        path = f"/{path}" if path else ""
    if site and (path == f"/{site}" or path.startswith(f"/{site}/")):
        return f"https://{host}{path}"
    if site:
        return f"https://{host}/{site}{path}"
    return f"https://{host}{path}"


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    host = company.host
    tenant = company.token
    site = company.site or "External"
    if not host or not tenant:
        return []
    url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
    referer = f"https://{host}/{site}"
    limit = 20
    searches = ["intern"]
    if company.category == "quant":
        searches = ["intern", "spring", "insight"]
    jobs: list[Job] = []
    seen: set[str] = set()
    for search_text in searches:
        offset = 0
        total = None
        while True:
            status, data = http.post_json(
                url,
                {"limit": limit, "offset": offset, "searchText": search_text},
                extra_headers={"Referer": referer},
            )
            if status != 200 or not isinstance(data, dict):
                break
            if total is None:
                reported = int(data.get("total") or 0)
                total = min(reported, 80) if reported else 0
            batch = data.get("jobPostings") or []
            for raw in batch:
                path = str(raw.get("externalPath") or "")
                loc = str(raw.get("locationsText") or "")
                title = str(raw.get("title") or "").strip()
                job_id = path or title
                if job_id in seen:
                    continue
                seen.add(job_id)
                jobs.append(
                    Job(
                        uid=uid("workday", tenant, job_id),
                        company=company.name,
                        category=company.category,
                        title=title,
                        location=loc or path.replace("/job/", "").replace("-", " "),
                        url=build_job_url(host, site, path),
                        source="workday",
                        published=str(raw.get("postedOn") or ""),
                    )
                )
            offset += len(batch)
            if not batch:
                break
            if total and offset >= total:
                break
            if offset > 200:
                break
    return jobs
