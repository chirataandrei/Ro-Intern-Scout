from __future__ import annotations

import re

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid

JOB_RE = re.compile(
    r'href="((?:https://[^"]+)?/jobs/(\d+)/[^"]*)"[^>]*>([^<]+)</a>',
    re.I,
)


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    host = company.host or f"careers-{company.token}.icims.com"
    host = host.replace("https://", "").replace("http://", "").split("/")[0]
    url = (
        f"https://{host}/jobs/search?ss=1&searchKeyword=intern"
        f"&searchRelation=keyword_all&in_iframe=1"
    )
    status, body = http.get(url, headers={"Accept": "text/html"})
    if status != 200:
        return []
    jobs: list[Job] = []
    seen: set[str] = set()
    for href, job_id, title in JOB_RE.findall(body):
        if job_id in seen:
            continue
        seen.add(job_id)
        apply = href if href.startswith("http") else f"https://{host}{href}"
        jobs.append(
            Job(
                uid=uid("icims", company.token, job_id),
                company=company.name,
                category=company.category,
                title=title.strip(),
                location="",
                url=apply.split("?")[0],
                source="icims",
            )
        )
    return jobs
