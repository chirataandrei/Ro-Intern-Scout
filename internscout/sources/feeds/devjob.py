from __future__ import annotations

import html as html_lib
import re

from internscout.http import HttpClient
from internscout.models import Job
from internscout.sources import uid

RSS_URL = "https://devjob.ro/rss"

ITEM_RE = re.compile(r"<item>(.*?)</item>", re.S)
TITLE_RE = re.compile(r"<title><!\[CDATA\[(.*?)\]\]></title>", re.S)
LINK_RE = re.compile(r"<link>(.*?)</link>", re.S)
# "Title @ Company [salary range]" — the trailing bracket is always present,
# even when the salary itself is unknown ("[? - ? RON]").
TITLE_COMPANY_RE = re.compile(r"^(.*?)\s@\s(.*?)\s\[[^\]]*\]\s*$", re.S)
SLUG_RE = re.compile(r"^https://devjob\.ro/jobs/([^?]+)")


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(text or "")).strip()


def parse_items(body: str) -> list[tuple[str, str, str, str]]:
    found: list[tuple[str, str, str, str]] = []
    seen: set[str] = set()
    for block in ITEM_RE.findall(body):
        title_m = TITLE_RE.search(block)
        link_m = LINK_RE.search(block)
        if not title_m or not link_m:
            continue
        raw_title = _clean(title_m.group(1))
        url = html_lib.unescape(link_m.group(1).strip())
        slug_m = SLUG_RE.match(url)
        if not slug_m:
            continue
        slug = slug_m.group(1)
        if slug in seen:
            continue
        seen.add(slug)
        split_m = TITLE_COMPANY_RE.match(raw_title)
        if split_m:
            title, company = split_m.group(1).strip(), split_m.group(2).strip()
        else:
            title, company = raw_title, ""
        found.append((slug, title, company, url))
    return found


def fetch_jobs(http: HttpClient) -> list[Job]:
    status, body = http.get(RSS_URL, headers={"Accept": "application/xml, text/xml"})
    if status != 200 or not body:
        return []
    jobs: list[Job] = []
    for job_id, title, company, url in parse_items(body):
        if not title:
            continue
        jobs.append(
            Job(
                uid=uid("devjob", "devjob", job_id),
                company=company or "Unknown company",
                category="aggregator",
                title=title,
                location="Romania",
                url=url,
                source="devjob",
            )
        )
    return jobs
