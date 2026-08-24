from __future__ import annotations

import html as html_lib
import re

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import careers, uid

HREF_RE = re.compile(
    r'<a[^>]+href="(/jobs/(\d+)[^"]*)"[^>]*>(.*?)</a>',
    re.I | re.S,
)
TAG_RE = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    text = html_lib.unescape(TAG_RE.sub(" ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    host = company.host or (f"https://{token}.freshteam.com/jobs" if token else "")
    if not host:
        return []
    if not host.startswith("http"):
        host = f"https://{host}"
    if "/jobs" not in host:
        host = host.rstrip("/") + "/jobs"
    # JSON-LD on the listing page is the cleanest public feed.
    careers_company = Company(
        name=company.name,
        category=company.category,
        ats="careers",
        token=token or company.name,
        host=host,
    )
    jsonld_jobs = careers.fetch_jobs(careers_company, http)
    if jsonld_jobs:
        out = []
        for job in jsonld_jobs:
            job.source = "freshteam"
            job.uid = job.uid.replace("careers:", "freshteam:", 1)
            out.append(job)
        return out

    status, body = http.get(host, headers={"Accept": "text/html"})
    if status != 200 or not body:
        return []
    jobs: list[Job] = []
    seen: set[str] = set()
    for href, job_id, inner in HREF_RE.findall(body):
        if job_id in seen:
            continue
        seen.add(job_id)
        title = _clean(inner)
        jobs.append(
            Job(
                uid=uid("freshteam", token, job_id),
                company=company.name,
                category=company.category,
                title=title,
                location="",
                url=href if href.startswith("http") else f"https://{token}.freshteam.com{href}",
                source="freshteam",
            )
        )
    return jobs
