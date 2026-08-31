from __future__ import annotations

import html as html_lib
import re

from internscout.http import HttpClient
from internscout.models import Job
from internscout.sources import uid

LIST_URLS = [
    "https://juniors.ro/jobs?q=internship",
    "https://juniors.ro/jobs?q=stagiu",
    "https://juniors.ro/jobs?q=intern",
    "https://juniors.ro/jobs?q=trainee",
]
ID_RE = re.compile(r"job_link_(\d+)")
TITLE_RE = re.compile(r"<h3>(.*?)</h3>", re.S | re.I)
STRONG_RE = re.compile(r"<strong>(.*?)</strong>", re.S | re.I)
LOGO_RE = re.compile(r'<img src="([^"]+company-logos/[^"]+)"', re.I)
TAG_RE = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    text = html_lib.unescape(TAG_RE.sub(" ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def company_from_logo(src: str) -> str:
    name = src.rstrip("/").split("/")[-1]
    name = re.sub(r"\.(png|jpe?g|webp|svg)$", "", name, flags=re.I)
    name = name.replace("-", " ").replace("_", " ").strip()
    return name.title() if name else "Unknown company"


def parse_listings(body: str) -> list[tuple[str, str, str, str]]:
    found: list[tuple[str, str, str, str]] = []
    seen: set[str] = set()
    for match in ID_RE.finditer(body):
        job_id = match.group(1)
        if job_id in seen:
            continue
        window = body[max(0, match.start() - 2800) : match.start() + 200]
        title_m = TITLE_RE.search(window)
        loc_m = STRONG_RE.search(window)
        logo_m = LOGO_RE.search(window)
        title = _clean(title_m.group(1) if title_m else "")
        if not title:
            continue
        location = _clean(loc_m.group(1) if loc_m else "Romania")
        if "|" in location:
            location = location.split("|", 1)[0].strip()
        company = company_from_logo(logo_m.group(1) if logo_m else "")
        seen.add(job_id)
        found.append((job_id, title, company, location or "Romania"))
    return found


def fetch_jobs(http: HttpClient) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    for url in LIST_URLS:
        status, body = http.get(url, headers={"Accept": "text/html"})
        if status != 200 or not body:
            continue
        for job_id, title, company, location in parse_listings(body):
            if job_id in seen:
                continue
            seen.add(job_id)
            jobs.append(
                Job(
                    uid=uid("juniors", "juniors", job_id),
                    company=company or "Unknown company",
                    category="aggregator",
                    title=title,
                    location=location,
                    url=f"https://juniors.ro/jobs/{job_id}/link",
                    source="juniors",
                )
            )
    return jobs
