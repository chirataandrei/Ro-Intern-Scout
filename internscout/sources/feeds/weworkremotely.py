from __future__ import annotations

import xml.etree.ElementTree as ET

from internscout.filters import is_student_entry, is_tech_role
from internscout.http import HttpClient
from internscout.models import Job
from internscout.sources import uid

FEED_URL = "https://weworkremotely.com/categories/remote-programming-jobs.rss"


def jobs_from_rss(xml_text: str) -> list[tuple[str, str, str, str, str]]:
    """Return (job_id, title, company, region, link) tuples."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    found: list[tuple[str, str, str, str, str]] = []
    for item in root.findall("./channel/item"):
        raw_title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or item.findtext("guid") or "").strip()
        region = (item.findtext("region") or "").strip()
        if not raw_title or not link:
            continue
        company, _, rest = raw_title.partition(":")
        title = rest.strip() if rest else raw_title
        company = company.strip() if rest else ""
        job_id = link.rstrip("/").rsplit("/", 1)[-1]
        found.append((job_id, title, company, region, link))
    return found


def fetch_jobs(http: HttpClient) -> list[Job]:
    status, body = http.get(FEED_URL, headers={"Accept": "application/rss+xml, text/xml"})
    if status != 200:
        return []
    jobs: list[Job] = []
    for job_id, title, company, region, link in jobs_from_rss(body):
        if not title or not is_student_entry(title) or not is_tech_role(title):
            continue
        location = f"Remote - {region}" if region else "Remote"
        jobs.append(
            Job(
                uid=uid("weworkremotely", "weworkremotely", job_id),
                company=company or "Unknown company",
                category="aggregator",
                title=title,
                location=location,
                url=link,
                source="weworkremotely",
            )
        )
    return jobs
