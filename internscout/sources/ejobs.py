from __future__ import annotations

import json
import re

from internscout.http import HttpClient
from internscout.models import Job
from internscout.sources import uid

LIST_URLS = [
    "https://www.ejobs.ro/locuri-de-munca/internship",
    "https://www.ejobs.ro/locuri-de-munca/it-software/internship",
    "https://www.ejobs.ro/locuri-de-munca/it-software",
]

LD_RE = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
    re.I | re.S,
)
JOB_PATH_RE = re.compile(r"/user/locuri-de-munca/([^/]+)/(\d+)")


def _jobs_from_ld(blob: str) -> list[tuple[str, str, str]]:
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return []
    entity = data.get("mainEntity") if isinstance(data, dict) else None
    if not isinstance(entity, dict):
        return []
    out: list[tuple[str, str, str]] = []
    for el in entity.get("itemListElement") or []:
        if not isinstance(el, dict):
            continue
        item = el.get("item") if isinstance(el.get("item"), dict) else el
        title = str(item.get("name") or "")
        url = str(el.get("url") or item.get("id") or item.get("url") or "")
        if not title or not url:
            continue
        out.append((title, url, url.rstrip("/").split("/")[-1]))
    return out


def fetch_jobs(http: HttpClient) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    for base in LIST_URLS:
        for page in range(1, 5):
            url = base if page == 1 else f"{base}?page={page}"
            status, body = http.get(url, headers={"Accept": "text/html"})
            if status != 200:
                break
            found: list[tuple[str, str, str]] = []
            for blob in LD_RE.findall(body):
                found.extend(_jobs_from_ld(blob))
            if not found:
                for path, job_id in JOB_PATH_RE.findall(body):
                    title = path.replace("-", " ")
                    found.append((title, f"https://www.ejobs.ro/user/locuri-de-munca/{path}/{job_id}", job_id))
            new = 0
            for title, job_url, job_id in found:
                if job_id in seen:
                    continue
                seen.add(job_id)
                new += 1
                jobs.append(
                    Job(
                        uid=uid("ejobs", "ejobs", job_id),
                        company="eJobs",
                        category="aggregator",
                        title=title.strip(),
                        location="Romania",
                        url=job_url if job_url.startswith("http") else f"https://www.ejobs.ro{job_url}",
                        source="ejobs",
                    )
                )
            if new == 0:
                break
    return jobs
