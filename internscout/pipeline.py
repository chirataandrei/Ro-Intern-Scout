"""Fetch + filter + dedupe every company and feed into one sorted job list.

Companies (direct ATS boards) and feeds (aggregators, free EU boards, Apify)
each run on their own thread pool via net.pool.run_parallel, sharing one
HttpClient with a per-host rate limiter — see net/pool.py and net/http.py.
"""

from __future__ import annotations

from internscout.catalog.loader import load_companies
from internscout.config import COVERAGE_PATH
from internscout.delivery.emailer import is_romania_job
from internscout.filters import keep_job
from internscout.models import Company, Job
from internscout.net.http import HttpClient
from internscout.net.pool import make_shared_http_client, run_parallel, safe_print
from internscout.sources.ats.registry import fetch_company
from internscout.sources.base import FeedSpec
from internscout.sources.feeds.registry import FEEDS
from internscout.store import fingerprint


def _fetch_company_jobs(company: Company, http: HttpClient) -> tuple[list[Job], dict]:
    try:
        raw_jobs = fetch_company(company, http)
    except Exception as exc:  # noqa: BLE001 — one bad company must not abort the scan
        safe_print(f"! {company.name} ({company.ats}): {exc}")
        return [], {"name": company.name, "category": company.category, "raw": 0, "kept": 0, "error": str(exc)}
    kept: list[Job] = []
    for job in raw_jobs:
        if keep_job(
            title=job.title,
            location=job.location,
            extra=f"{job.url} {job.company}",
            category=job.category,
            company=job.company,
            from_aggregator=False,
        ):
            kept.append(job)
    safe_print(f"· {company.name:28} sites={len(company.sites):2} raw={len(raw_jobs):4} kept={len(kept):3}")
    return kept, {"name": company.name, "category": company.category, "raw": len(raw_jobs), "kept": len(kept)}


def _write_coverage(rows: list[dict]) -> None:
    from datetime import datetime, timezone
    import json

    COVERAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "companies": rows,
    }
    COVERAGE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _fetch_companies(http: HttpClient, companies: list[Company] | None = None) -> list[Job]:
    companies = companies if companies is not None else load_companies()
    results = run_parallel(companies, lambda company: _fetch_company_jobs(company, http))
    collected: list[Job] = []
    coverage: list[dict] = []
    for jobs, stats in results:
        collected.extend(jobs)
        coverage.append(stats)
    _write_coverage(coverage)
    return collected


def _fetch_feed_jobs(spec: FeedSpec, http: HttpClient) -> list[Job]:
    try:
        raw_jobs = spec.fetch(http)
    except Exception as exc:  # noqa: BLE001
        safe_print(f"! {spec.label}: {exc}")
        raw_jobs = []
    kept: list[Job] = []
    for job in raw_jobs:
        if keep_job(
            title=job.title,
            location=job.location,
            extra=job.company,
            category=job.category,
            company=job.company,
            from_aggregator=spec.from_aggregator,
            already_romania=spec.already_romania,
            assume_internship=spec.assume_internship,
        ):
            kept.append(job)
    safe_print(f"· {spec.label:28} {spec.source:16} raw={len(raw_jobs):4} kept={len(kept):3}")
    return kept


def _fetch_feeds(http: HttpClient, feeds: list[FeedSpec] | None = None) -> list[Job]:
    feeds = FEEDS if feeds is None else feeds
    results = run_parallel(feeds, lambda spec: _fetch_feed_jobs(spec, http))
    collected: list[Job] = []
    for jobs in results:
        collected.extend(jobs)
    return collected


def dedupe(jobs: list[Job]) -> list[Job]:
    """uid dedupe first, then a fingerprint pass.

    `jobs` here is [companies..., feeds...] — feeds are appended last and
    FEEDS lists Apify's feed at the very end (see apify_scout), so on a
    fingerprint collision the direct-ATS or earlier-feed posting always wins
    and the later duplicate (frequently the Apify one) is dropped.
    """
    seen_uid: set[str] = set()
    seen_fp: set[str] = set()
    out: list[Job] = []
    for job in jobs:
        if job.uid in seen_uid:
            continue
        fp = fingerprint(job)
        if fp in seen_fp:
            continue
        seen_uid.add(job.uid)
        seen_fp.add(fp)
        out.append(job)
    return out


def scan(http: HttpClient | None = None) -> list[Job]:
    http = http or make_shared_http_client()
    collected = _fetch_companies(http)
    collected.extend(_fetch_feeds(http))
    collected.sort(key=lambda j: (0 if is_romania_job(j) else 1, j.company.lower(), j.title.lower()))
    return dedupe(collected)
