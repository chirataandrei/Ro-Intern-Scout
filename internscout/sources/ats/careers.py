from __future__ import annotations

import json
import re

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid

JSONLD_RE = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
    re.I | re.S,
)


def _loc_text(node: dict) -> str:
    loc = node.get("jobLocation") or {}
    if isinstance(loc, list):
        parts = [_loc_text({"jobLocation": item}) for item in loc if isinstance(item, dict)]
        return ", ".join(p for p in parts if p)
    if not isinstance(loc, dict):
        return str(loc or "")
    addr = loc.get("address") if isinstance(loc.get("address"), dict) else loc
    bits = [
        str(addr.get("addressLocality") or ""),
        str(addr.get("addressRegion") or ""),
        str(addr.get("addressCountry") or loc.get("name") or ""),
    ]
    return ", ".join(x for x in bits if x)


def jobs_from_jsonld(blob: str, company: Company) -> list[Job]:
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return []
    nodes = data if isinstance(data, list) else [data]
    out: list[Job] = []
    stack = list(nodes)
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        if isinstance(node.get("@graph"), list):
            stack.extend(node["@graph"])
        if str(node.get("@type") or "") not in {"JobPosting", "jobposting"}:
            continue
        title = str(node.get("title") or "").strip()
        url = str(node.get("url") or node.get("@id") or "").strip()
        if not title or not url:
            continue
        org = node.get("hiringOrganization")
        firm = company.name
        if isinstance(org, dict) and org.get("name"):
            firm = str(org["name"])
        job_id = url.rstrip("/").split("/")[-1] or title
        out.append(
            Job(
                uid=uid("careers", company.token or company.name, job_id),
                company=firm,
                category=company.category,
                title=title,
                location=_loc_text(node),
                url=url,
                source="careers",
                published=str(node.get("datePosted") or ""),
            )
        )
    return out


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    url = (company.host or company.token or "").strip()
    if not url:
        return []
    if not url.startswith("http"):
        url = f"https://{url}"
    status, body = http.get(url, headers={"Accept": "text/html"})
    if status != 200:
        return []
    jobs: list[Job] = []
    seen: set[str] = set()
    for blob in JSONLD_RE.findall(body):
        for job in jobs_from_jsonld(blob, company):
            if job.uid in seen:
                continue
            seen.add(job.uid)
            jobs.append(job)
    return jobs
