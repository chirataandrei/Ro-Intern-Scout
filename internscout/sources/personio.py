from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid

JOB_HREF_RE = re.compile(r'href="(https?://[^"]+/job/[^"]+)"', re.I)


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1].lower()


def _text(node: ET.Element | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def _from_xml(body: str, company: Company) -> list[Job]:
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return []
    jobs: list[Job] = []
    for pos in root.iter():
        if _local(pos.tag) != "position":
            continue
        fields = {_local(child.tag): child for child in list(pos)}
        title = _text(fields.get("name") or fields.get("title"))
        job_id = _text(fields.get("id") or fields.get("officeid")) or title
        office = fields.get("office")
        office_name = _text(office) if office is not None and office.text else ""
        if office is not None and not office_name:
            office_name = " ".join(
                _text(child) for child in list(office) if _text(child)
            )
        url = _text(fields.get("url") or fields.get("applyurl"))
        if not url:
            url = f"https://{company.token}.jobs.personio.com/job/{job_id}"
        if not title:
            continue
        jobs.append(
            Job(
                uid=uid("personio", company.token, job_id),
                company=company.name,
                category=company.category,
                title=title,
                location=office_name,
                url=url,
                source="personio",
            )
        )
    return jobs


def _from_html(body: str, company: Company) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    for href in JOB_HREF_RE.findall(body):
        job_id = href.rstrip("/").split("/")[-1]
        if not job_id or job_id in seen:
            continue
        seen.add(job_id)
        title = job_id.replace("-", " ")
        jobs.append(
            Job(
                uid=uid("personio", company.token, job_id),
                company=company.name,
                category=company.category,
                title=title,
                location="",
                url=href.split("?")[0],
                source="personio",
            )
        )
    return jobs


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    if not token:
        return []
    for url in (
        f"https://{token}.jobs.personio.com/xml",
        f"https://{token}.jobs.personio.de/xml",
        f"https://{token}.jobs.personio.com/",
        f"https://{token}.jobs.personio.de/",
    ):
        status, body = http.get(url, headers={"Accept": "application/xml, text/html"})
        if status != 200 or not body:
            continue
        jobs = _from_xml(body, company) if "<position" in body.lower() else _from_html(body, company)
        if jobs:
            return jobs
    return []
