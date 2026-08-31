"""Loads the company catalog from sharded JSON files under catalog/data/companies/.

Adding a firm touches exactly one shard (its category), so diffs stay small
and the bot that commits data/seen.json never collides with manual catalog
edits. A single company.json (legacy) is still honored as a fallback if the
shard directory is empty, so older checkouts / tools keep working.
"""

from __future__ import annotations

import json
from pathlib import Path

from internscout.catalog.naming import board_public_url, official_urls
from internscout.config import COMPANIES_DIR, COMPANIES_PATH
from internscout.models import Company

VALID_CATEGORIES = {
    "faang",
    "quant",
    "finance",
    "rd",
    "product",
    "ssc",
    "gaming",
    "telecom",
    "other",
    "discovered",
    "aggregator",
}


def _company_urls(row: dict) -> list[str]:
    urls: list[str] = []
    for site in row.get("sites") or []:
        if not isinstance(site, dict):
            continue
        url = str(site.get("url") or "") or board_public_url(
            str(site.get("ats") or ""),
            str(site.get("token") or ""),
            str(site.get("host") or ""),
            str(site.get("site") or ""),
        )
        if url:
            urls.append(url)
    if not urls and row.get("ats"):
        url = board_public_url(
            str(row.get("ats") or ""),
            str(row.get("token") or ""),
            str(row.get("host") or ""),
            str(row.get("site") or ""),
        )
        if url:
            urls.append(url)
    urls.extend(official_urls(str(row.get("name") or "")))
    seen: set[str] = set()
    out: list[str] = []
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            out.append(url)
    return out


def _shard_paths() -> list[Path]:
    if not COMPANIES_DIR.exists():
        return []
    return sorted(COMPANIES_DIR.glob("*.json"))


def load_companies_raw() -> list[dict]:
    """Merged, deduplicated, ``urls``-enriched company rows across all shards."""
    rows: list[dict] = []
    shards = _shard_paths()
    if shards:
        for path in shards:
            data = json.loads(path.read_text(encoding="utf-8"))
            items = data.get("companies") if isinstance(data, dict) else data
            rows.extend(items or [])
    elif COMPANIES_PATH.exists():
        data = json.loads(COMPANIES_PATH.read_text(encoding="utf-8"))
        items = data.get("companies") if isinstance(data, dict) else data
        rows.extend(items or [])

    by_name: dict[str, dict] = {}
    for row in rows:
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        row = dict(row)
        if not row.get("urls"):
            row["urls"] = _company_urls(row)
        by_name.setdefault(name, row)
    return list(by_name.values())


def load_companies() -> list[Company]:
    return [Company.from_dict(row) for row in load_companies_raw()]
