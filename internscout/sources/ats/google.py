from __future__ import annotations

import json
import re

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid

SEARCH_URLS = [
    "https://www.google.com/about/careers/applications/jobs/results/?q=intern%20Bucharest",
    "https://www.google.com/about/careers/applications/jobs/results/?q=intern&location=Romania",
    "https://www.google.com/about/careers/applications/jobs/results/?q=Software%20Engineering%20Intern&location=Bucharest",
]

JSONLD_RE = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
    re.I | re.S,
)
def _jobs_from_jsonld(blob: str, company: Company) -> list[Job]:
    jobs: list[Job] = []
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return jobs
    items = data if isinstance(data, list) else [data]
    for item in items:
        if not isinstance(item, dict):
            continue
        graph = item.get("@graph") if item.get("@type") != "JobPosting" else [item]
        if not graph:
            if str(item.get("@type") or "") == "JobPosting":
                graph = [item]
            else:
                continue
        for node in graph:
            if not isinstance(node, dict):
                continue
            if str(node.get("@type") or "") != "JobPosting":
                continue
            loc = node.get("jobLocation") or {}
            loc_text = ""
            if isinstance(loc, dict):
                addr = loc.get("address") or {}
                if isinstance(addr, dict):
                    loc_text = " ".join(
                        str(addr.get(k) or "")
                        for k in ("addressLocality", "addressRegion", "addressCountry")
                    )
            elif isinstance(loc, list):
                loc_text = json.dumps(loc)
            url = str(node.get("url") or "")
            job_id = url.rstrip("/").split("/")[-1] or str(node.get("title") or "")
            jobs.append(
                Job(
                    uid=uid("google", "google", job_id),
                    company=company.name,
                    category=company.category,
                    title=str(node.get("title") or "").strip(),
                    location=loc_text,
                    url=url,
                    source="google",
                    published=str(node.get("datePosted") or ""),
                )
            )
    return jobs


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    for url in SEARCH_URLS:
        status, body = http.get(url, headers={"Accept": "text/html"})
        if status != 200:
            continue
        for blob in JSONLD_RE.findall(body):
            for job in _jobs_from_jsonld(blob, company):
                if job.uid in seen:
                    continue
                seen.add(job.uid)
                jobs.append(job)
    return jobs
