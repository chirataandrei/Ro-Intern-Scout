from __future__ import annotations

import re

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import uid

COMPANY_ID_RE = re.compile(r'"company"\s*:\s*\{\s*"id"\s*:\s*(\d+)', re.I)
COMPANY_ID_FALLBACK_RE = re.compile(r'"companyId"\s*:\s*(\d+)', re.I)


def company_id_from_html(body: str) -> str:
    match = COMPANY_ID_RE.search(body) or COMPANY_ID_FALLBACK_RE.search(body)
    return match.group(1) if match else ""


def _loc(raw: dict) -> str:
    bits: list[str] = []
    for loc in raw.get("locations") or []:
        if isinstance(loc, dict):
            bits.extend(
                str(x)
                for x in (
                    loc.get("city"),
                    loc.get("name"),
                    (loc.get("country") or {}).get("name") if isinstance(loc.get("country"), dict) else loc.get("country"),
                )
                if x
            )
        else:
            bits.append(str(loc))
    remote = raw.get("remoteOption") or raw.get("workplaceType") or ""
    if remote:
        bits.append(str(remote))
    return ", ".join(x for x in bits if x)


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    token = company.token
    company_id = str(company.extra.get("company_id") or company.extra.get("id") or "")
    if not company_id and token:
        status, body = http.get(f"https://join.com/companies/{token}", headers={"Accept": "text/html"})
        if status == 200:
            company_id = company_id_from_html(body)
    if not company_id:
        return []
    jobs: list[Job] = []
    seen: set[str] = set()
    for page in range(1, 12):
        status, data = http.get_json(
            f"https://join.com/api/public/companies/{company_id}/jobs"
            f"?locale=en-us&page={page}&pageSize=5"
        )
        if status != 200 or not isinstance(data, dict):
            break
        items = data.get("items") or []
        for raw in items:
            if not isinstance(raw, dict):
                continue
            job_id = str(raw.get("id") or raw.get("idParam") or "")
            if not job_id or job_id in seen:
                continue
            seen.add(job_id)
            slug = str(raw.get("idParam") or job_id)
            jobs.append(
                Job(
                    uid=uid("join", token or company_id, job_id),
                    company=company.name,
                    category=company.category,
                    title=str(raw.get("title") or raw.get("name") or "").strip(),
                    location=_loc(raw),
                    url=str(
                        raw.get("shareableUrl")
                        or raw.get("url")
                        or f"https://join.com/companies/{token}/jobs/{slug}"
                    ),
                    source="join",
                    published=str(raw.get("publishedAt") or raw.get("createdAt") or ""),
                )
            )
        pagination = data.get("pagination") or {}
        page_count = int(pagination.get("pageCount") or pagination.get("totalPages") or 0)
        if not items or (page_count and page >= page_count):
            break
    return jobs
