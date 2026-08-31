from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid

JOB_HREF_RE = re.compile(
    r'href="(https?://[^"]+/(?:job|jobs|vacancy|stellenangebote)/[^"]+)"',
    re.I,
)


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1].lower()


def _text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    bits = [node.text or ""]
    bits.extend(_text(child) for child in list(node))
    bits.append(node.tail or "")
    return re.sub(r"\s+", " ", " ".join(bits)).strip()


def _from_xml(body: str, company: Company) -> list[Job]:
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return []
    jobs: list[Job] = []
    seen: set[str] = set()
    for node in root.iter():
        tag = _local(node.tag)
        if tag not in {"job", "position", "item", "vacancy"}:
            continue
        fields = {_local(child.tag): child for child in list(node)}
        title = _text(fields.get("title") or fields.get("name") or fields.get("jobtitle"))
        url = _text(fields.get("url") or fields.get("link") or fields.get("applyurl"))
        loc = _text(fields.get("location") or fields.get("city") or fields.get("workplace"))
        job_id = _text(fields.get("id") or fields.get("jobid")) or (url.rstrip("/").split("/")[-1] if url else title)
        if not title or not job_id or job_id in seen:
            continue
        seen.add(job_id)
        jobs.append(
            Job(
                uid=uid("softgarden", company.token, job_id),
                company=company.name,
                category=company.category,
                title=title,
                location=loc,
                url=url or f"https://{company.token}.jobs.softgarden.io/",
                source="softgarden",
            )
        )
    return jobs


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    host = (company.host or "").strip().rstrip("/")
    urls: list[str] = []
    if host.startswith("http"):
        urls.extend(
            [
                f"{host}/feed/xml",
                f"{host}/export/xml",
                f"{host}/jobxml",
                host,
            ]
        )
    if token:
        urls.extend(
            [
                f"https://{token}.jobs.softgarden.io/feed/xml",
                f"https://{token}.jobs.softgarden.de/feed/xml",
                f"https://{token}.softgarden.io/jobxml",
                f"https://{token}.jobs.softgarden.io/",
                f"https://{token}.jobs.softgarden.de/",
            ]
        )
    seen_urls: set[str] = set()
    for url in urls:
        if url in seen_urls:
            continue
        seen_urls.add(url)
        status, body = http.get(url, headers={"Accept": "application/xml, text/xml, text/html"})
        if status != 200 or not body:
            continue
        if "<" in body and any(tag in body.lower() for tag in ("<job", "<position", "<item", "<vacancy")):
            jobs = _from_xml(body, company)
            if jobs:
                return jobs
        if "href=" in body:
            jobs: list[Job] = []
            seen: set[str] = set()
            for href in JOB_HREF_RE.findall(body):
                job_id = href.rstrip("/").split("/")[-1]
                if not job_id or job_id in seen:
                    continue
                seen.add(job_id)
                jobs.append(
                    Job(
                        uid=uid("softgarden", token, job_id),
                        company=company.name,
                        category=company.category,
                        title=job_id.replace("-", " "),
                        location="",
                        url=href.split("?")[0],
                        source="softgarden",
                    )
                )
            if jobs:
                return jobs
    return []
