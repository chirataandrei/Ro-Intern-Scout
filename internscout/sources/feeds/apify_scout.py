"""Read-only Apify cache → Job list.

The daily scan never talks to Apify. ``apify-refresh`` (and the dedicated
GitHub Action) write ``data/apify_cache.json``; this fetcher only reads it.
``from_aggregator=False`` because Wellfound/LinkedIn locations are real —
we must not assume a missing city means Romania.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from internscout.config import APIFY_CACHE_PATH
from internscout.http import HttpClient
from internscout.models import Job
from internscout.sources import uid


def _load_cache() -> dict[str, Any]:
    if not APIFY_CACHE_PATH.exists():
        return {}
    try:
        payload = json.loads(APIFY_CACHE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _nested_name(value: Any, *keys: str) -> str:
    if isinstance(value, str):
        return value.strip()
    if not isinstance(value, dict):
        return ""
    for key in keys:
        inner = value.get(key)
        if isinstance(inner, str) and inner.strip():
            return inner.strip()
        if isinstance(inner, dict):
            nested = _nested_name(inner, *keys)
            if nested:
                return nested
    return ""


def _company_name(item: dict[str, Any]) -> str:
    for key in ("companyName", "company_name"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for key in ("company", "startup", "organization"):
        name = _nested_name(item.get(key), "name", "title")
        if name:
            return name
    return ""


def _job_id(item: dict[str, Any], url: str) -> str:
    for key in ("id", "jobId", "job_id", "uuid", "slug"):
        value = item.get(key)
        if value:
            return str(value)
    if url:
        path = urlparse(url).path.rstrip("/").split("/")
        if path and path[-1]:
            return path[-1]
    return ""


def _clean_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    tracking = {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "ref", "source"}
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=False) if k not in tracking]
    return urlunparse(parsed._replace(query=urlencode(query), fragment=""))


def _location(item: dict[str, Any]) -> str:
    loc = item.get("location") or item.get("locations") or ""
    if isinstance(loc, list):
        loc = ", ".join(str(x) for x in loc if x)
    elif isinstance(loc, dict):
        loc = " ".join(str(loc.get(k) or "") for k in ("city", "name", "country", "label") if loc.get(k))
    loc = str(loc or "").strip()
    workplace = str(item.get("workplaceType") or item.get("workplace") or item.get("remote") or "")
    if str(workplace).lower() in {"remote", "true", "1"} and "remote" not in loc.lower():
        loc = f"{loc} Remote".strip()
    if item.get("isRemote") and "remote" not in loc.lower():
        loc = f"{loc} Remote".strip()
    return loc


def _to_job(item: dict[str, Any]) -> Job | None:
    if not isinstance(item, dict):
        return None
    title = str(item.get("title") or item.get("jobTitle") or "").strip()
    url = _clean_url(str(item.get("url") or item.get("jobUrl") or item.get("applyUrl") or item.get("link") or ""))
    if not title or not url:
        return None
    company = _company_name(item) or "Unknown company"
    query_id = str(item.get("query_id") or item.get("queryId") or "wellfound")
    job_id = _job_id(item, url)
    if not job_id:
        return None
    category = str(item.get("category") or "product")
    return Job(
        uid=uid("apify", query_id, job_id),
        company=company,
        category=category,
        title=title,
        location=_location(item),
        url=url,
        source="apify",
        published=str(item.get("postedAt") or item.get("publishedAt") or item.get("published") or ""),
    )


def fetch_jobs(http: HttpClient) -> list[Job]:  # noqa: ARG001 — signature matches FeedSpec
    payload = _load_cache()
    jobs: list[Job] = []
    seen: set[str] = set()
    for item in payload.get("items") or []:
        job = _to_job(item)
        if job is None or job.uid in seen:
            continue
        seen.add(job.uid)
        jobs.append(job)
    return jobs
