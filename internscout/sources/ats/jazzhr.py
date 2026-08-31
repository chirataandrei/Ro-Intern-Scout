from __future__ import annotations

import html as html_lib
import re

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid

JOB_RE = re.compile(
    r'href="(https?://[^"]+\.applytojob\.com/apply/([^"/]+)/([^"]+))"',
    re.I,
)
TAG_RE = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    text = html_lib.unescape(TAG_RE.sub(" ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    if not token:
        return []
    status, body = http.get(
        f"https://{token}.applytojob.com/apply",
        headers={"Accept": "text/html"},
    )
    if status != 200 or not body:
        return []
    jobs: list[Job] = []
    seen: set[str] = set()
    for href, job_id, slug in JOB_RE.findall(body):
        if job_id in seen:
            continue
        seen.add(job_id)
        title = _clean(slug.replace("-", " "))
        jobs.append(
            Job(
                uid=uid("jazzhr", token, job_id),
                company=company.name,
                category=company.category,
                title=title,
                location="",
                url=href.split("?")[0],
                source="jazzhr",
            )
        )
    return jobs
