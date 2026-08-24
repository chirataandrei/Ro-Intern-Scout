from __future__ import annotations

import re

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid
from internscout.sources.careers import _loc_text

JOB_RE = re.compile(
    r'<item>.*?<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>.*?'
    r'<link>(.*?)</link>',
    re.I | re.S,
)


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    jobs: list[Job] = []

    status, data = http.get_json(f"https://{token}.teamtailor.com/jobs.json")
    if status == 200 and isinstance(data, dict):
        items = data.get("items") or data.get("jobs") or data.get("data") or []
        for raw in items:
            if not isinstance(raw, dict):
                continue
            attrs = raw.get("attributes") if isinstance(raw.get("attributes"), dict) else raw
            jp = raw.get("_jobposting") if isinstance(raw.get("_jobposting"), dict) else {}
            job_id = str(raw.get("id") or attrs.get("id") or attrs.get("slug") or "")
            loc = attrs.get("locations") or attrs.get("location") or ""
            if isinstance(loc, list):
                loc = ", ".join(str(x) for x in loc)
            if not loc and jp:
                loc = _loc_text(jp)
            jobs.append(
                Job(
                    uid=uid("teamtailor", token, job_id),
                    company=company.name,
                    category=company.category,
                    title=str(attrs.get("title") or raw.get("title") or jp.get("title") or "").strip(),
                    location=str(loc),
                    url=str(attrs.get("url") or raw.get("url") or jp.get("url") or f"https://{token}.teamtailor.com/jobs/{job_id}"),
                    source="teamtailor",
                    published=str(raw.get("date_published") or attrs.get("published-at") or ""),
                )
            )
        if jobs:
            return jobs

    status, body = http.get(f"https://{token}.teamtailor.com/jobs.rss")
    if status != 200:
        return []
    for title, link in JOB_RE.findall(body):
        title = title.strip()
        link = link.strip()
        job_id = link.rstrip("/").split("/")[-1] or title
        jobs.append(
            Job(
                uid=uid("teamtailor", token, job_id),
                company=company.name,
                category=company.category,
                title=title,
                location="",
                url=link,
                source="teamtailor",
            )
        )
    return jobs
