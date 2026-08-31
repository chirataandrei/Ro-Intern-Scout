from __future__ import annotations

import html as html_lib
import re

from internscout.http import HttpClient
from internscout.models import Job
from internscout.sources import uid

LIST_URL = "https://www.stagiipebune.ro/students/jobs/"
JOB_HREF_RE = re.compile(
    r'href="(/jobs/([^/]+)/([^"]+))"[^>]*>([^<]+)</a>',
    re.I,
)
COMPANY_RE = re.compile(r'company_profile/[^"]+"[^>]*>([^<]+)</a>', re.I)
MUTED_RE = re.compile(r'<span class="muted">([^<]*)</span>', re.I)
TBODY_RE = re.compile(
    r'<tbody class="job-table-body[^"]*">(.*?)</tbody>',
    re.I | re.S,
)
TAG_RE = re.compile(r"<[^>]+>")
DATE_RE = re.compile(r"^\d{1,2}\s+\w+", re.I)


def _clean(text: str) -> str:
    text = html_lib.unescape(TAG_RE.sub(" ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def _location(spans: list[str]) -> str:
    for raw in reversed(spans):
        text = _clean(raw)
        if not text:
            continue
        folded = text.lower()
        if folded.startswith("plătit") or folded.startswith("platit") or folded.startswith("paid"):
            continue
        if DATE_RE.match(text):
            continue
        return text
    return "Romania"


def parse_listings(body: str) -> list[tuple[str, str, str, str, str]]:
    found: list[tuple[str, str, str, str, str]] = []
    seen: set[str] = set()
    blocks = TBODY_RE.findall(body) or [body]
    for block in blocks:
        title_m = JOB_HREF_RE.search(block)
        if not title_m:
            continue
        href, slug, job_slug, title = title_m.groups()
        job_id = job_slug or href
        if job_id in seen:
            continue
        seen.add(job_id)
        company_m = COMPANY_RE.search(block)
        company = _clean(company_m.group(1) if company_m else slug.replace("-", " "))
        location = _location(MUTED_RE.findall(block))
        found.append((job_id, _clean(title), company, location, href))
    return found


def fetch_jobs(http: HttpClient) -> list[Job]:
    status, body = http.get(LIST_URL, headers={"Accept": "text/html"})
    if status != 200:
        return []
    jobs: list[Job] = []
    for job_id, title, company, location, href in parse_listings(body):
        jobs.append(
            Job(
                uid=uid("stagiipebune", "stagiipebune", job_id),
                company=company or "Unknown company",
                category="aggregator",
                title=title,
                location=location or "Romania",
                url=f"https://www.stagiipebune.ro{href}",
                source="stagiipebune",
            )
        )
    return jobs
