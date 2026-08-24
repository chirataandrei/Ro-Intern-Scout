from __future__ import annotations

import re

from internscout.http import HttpClient
from internscout.models import Job
from internscout.sources import uid
from internscout.sources.careers import jobs_from_jsonld

SITEMAP_URL = "https://www.undelucram.ro/sitemaps/jobs-sitemap-ro-1.xml"
JSONLD_RE = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
    re.I | re.S,
)
INTERN_SLUG_RE = re.compile(
    r"(internship|stagiu|stagiar|trainee|practicant|practica|intern(?:ship)?s?)(?:[-/]|$)",
    re.I,
)
INTERNAL_RE = re.compile(r"internal[-_]?(?:auditor|audit|control)", re.I)
LOC_RE = re.compile(r"<loc>([^<]+)</loc>", re.I)
APPLY_RE = re.compile(
    r'href="(https?://(?:jobs\.smartrecruiters\.com|apply\.workable\.com|job-boards\.greenhouse\.io|jobs\.lever\.co|jobs\.ashbyhq\.com)[^"]+)"',
    re.I,
)
MAX_DETAIL_PAGES = 40


def intern_job_urls(sitemap_xml: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for loc in LOC_RE.findall(sitemap_xml):
        if "/locuri-de-munca/" not in loc and "/jobs/" not in loc:
            continue
        if "?" in loc:
            continue
        if INTERNAL_RE.search(loc):
            continue
        if not INTERN_SLUG_RE.search(loc):
            continue
        if loc in seen:
            continue
        seen.add(loc)
        urls.append(loc)
    return urls


def jobs_from_detail(html: str, page_url: str) -> list[Job]:
    from internscout.models import Company

    dummy = Company(name="Unknown company", category="aggregator", ats="careers", token="undelucram")
    jobs: list[Job] = []
    seen: set[str] = set()
    for blob in JSONLD_RE.findall(html):
        for job in jobs_from_jsonld(blob, dummy):
            job.source = "undelucram"
            job.category = "aggregator"
            job.uid = uid("undelucram", "undelucram", job.uid.split(":")[-1] or job.url)
            apply_m = APPLY_RE.search(html)
            if apply_m:
                job.url = apply_m.group(1)
            elif not job.url:
                job.url = page_url
            if job.uid in seen:
                continue
            seen.add(job.uid)
            jobs.append(job)
    return jobs


def fetch_jobs(http: HttpClient) -> list[Job]:
    status, sitemap = http.get(SITEMAP_URL, headers={"Accept": "application/xml, text/xml"})
    if status != 200 or not sitemap:
        return []
    jobs: list[Job] = []
    seen: set[str] = set()
    for url in intern_job_urls(sitemap)[:MAX_DETAIL_PAGES]:
        status, body = http.get(url, headers={"Accept": "text/html"})
        if status != 200 or not body:
            continue
        for job in jobs_from_detail(body, url):
            if job.uid in seen:
                continue
            seen.add(job.uid)
            if not job.url:
                job.url = url
            jobs.append(job)
    return jobs
