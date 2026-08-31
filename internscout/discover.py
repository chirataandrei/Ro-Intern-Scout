"""Apify-powered ATS board discovery and Wellfound cache refresh.

Discovery is a one-time cost: Google ``site:`` queries find (ats, token)
pairs, we probe them with the real fetchers, and from then on the daily
scan hits those boards for free. Wellfound listings are written to
``data/apify_cache.json`` and read later by ``sources.feeds.apify_scout``
with no Apify call on the scan path.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from internscout.catalog.naming import board_public_url
from internscout.config import (
    APIFY_CACHE_PATH,
    APIFY_QUERIES_PATH,
    DISCOVERED_PATH,
    apify_actor_discovery,
    apify_actor_wellfound,
)
from internscout.net.apify import ApifyClient, ApifyState, guarded_run

BOARD_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"jobs\.ashbyhq\.com/([^/?#]+)", re.I), "ashby"),
    (re.compile(r"job-boards\.greenhouse\.io/([^/?#]+)", re.I), "greenhouse"),
    (re.compile(r"boards\.greenhouse\.io/([^/?#]+)", re.I), "greenhouse"),
    (re.compile(r"jobs\.lever\.co/([^/?#]+)", re.I), "lever"),
    (re.compile(r"apply\.workable\.com/([^/?#]+)", re.I), "workable"),
    (re.compile(r"([^./]+)\.recruitee\.com", re.I), "recruitee"),
    (re.compile(r"([^./]+)\.jobs\.personio\.com", re.I), "personio"),
    (re.compile(r"([^./]+)\.breezy\.hr", re.I), "breezy"),
    (re.compile(r"([^./]+)\.teamtailor\.com", re.I), "teamtailor"),
    (re.compile(r"join\.com/companies/([^/?#]+)", re.I), "join"),
    (re.compile(r"ats\.rippling\.com/([^/?#]+)", re.I), "rippling"),
]

DISCOVERY_QUERIES = [
    'site:jobs.ashbyhq.com (intern OR internship OR stagiu) (Romania OR Bucharest OR "Remote - Europe")',
    'site:job-boards.greenhouse.io intern (Romania OR "Remote Europe")',
    'site:jobs.lever.co internship (Bucharest OR "Remote - EU")',
    'site:apply.workable.com (stagiu OR internship) (Romania OR "Remote, Europe")',
    "site:recruitee.com internship Romania",
    'site:jobs.personio.com (Praktikum OR internship) "remote europe"',
    'site:join.com internship "remote europe"',
    "site:breezy.hr internship Romania",
    'site:teamtailor.com internship "remote europe"',
    "site:ats.rippling.com internship europe",
]

# Google Search Scraper: $0.0045/page + $0.001/run. 10 queries × 2 pages.
DISCOVERY_COST_USD = 10 * 2 * 0.0045 + 0.001
WELLFOUND_COST_PER_ROW = 0.00099
GOOGLE_COST_PER_PAGE = 0.0045


def extract_board(url: str) -> tuple[str, str] | None:
    """Return (ats, token) for a public board URL, or None."""
    if not url:
        return None
    for pattern, ats in BOARD_PATTERNS:
        match = pattern.search(url)
        if match:
            token = match.group(1).strip().strip("/")
            if token:
                return ats, token
    return None


def _urls_from_serp_item(item: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    for key in ("url", "link", "organicUrl", "displayedUrl"):
        value = item.get(key)
        if isinstance(value, str) and value.startswith("http"):
            urls.append(value)
    organic = item.get("organicResults") or item.get("organic") or []
    if isinstance(organic, list):
        for row in organic:
            if isinstance(row, dict):
                urls.extend(_urls_from_serp_item(row))
            elif isinstance(row, str) and row.startswith("http"):
                urls.append(row)
    return urls


def boards_from_serp(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, str]] = []
    for item in items:
        for url in _urls_from_serp_item(item):
            parsed = extract_board(url)
            if not parsed:
                continue
            ats, token = parsed
            key = (ats, token.lower())
            if key in seen:
                continue
            seen.add(key)
            out.append({"ats": ats, "token": token, "url": board_public_url(ats, token), "source_url": url})
    return out


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _known_ats_tokens() -> set[tuple[str, str]]:
    from internscout.catalog.loader import load_companies_raw

    known: set[tuple[str, str]] = set()
    for row in load_companies_raw():
        for site in row.get("sites") or []:
            if not isinstance(site, dict):
                continue
            ats = str(site.get("ats") or "").lower()
            token = str(site.get("token") or "").lower()
            if ats and token:
                known.add((ats, token))
        ats = str(row.get("ats") or "").lower()
        token = str(row.get("token") or "").lower()
        if ats and token:
            known.add((ats, token))
    pending = _load_json(DISCOVERED_PATH, {})
    for item in pending.get("boards") if isinstance(pending, dict) else pending or []:
        if isinstance(item, dict):
            ats = str(item.get("ats") or "").lower()
            token = str(item.get("token") or "").lower()
            if ats and token:
                known.add((ats, token))
    return known


def merge_discovered(boards: list[dict[str, str]]) -> list[dict[str, str]]:
    known = _known_ats_tokens()
    existing = _load_json(DISCOVERED_PATH, {"boards": []})
    if isinstance(existing, list):
        existing = {"boards": existing}
    current = list(existing.get("boards") or [])
    new_boards: list[dict[str, str]] = []
    for board in boards:
        key = (board["ats"].lower(), board["token"].lower())
        if key in known:
            continue
        known.add(key)
        entry = {
            "ats": board["ats"],
            "token": board["token"],
            "url": board.get("url") or board_public_url(board["ats"], board["token"]),
            "name": board["token"],
            "category": "discovered",
            "found_at": datetime.now(timezone.utc).isoformat(),
        }
        current.append(entry)
        new_boards.append(entry)
    DISCOVERED_PATH.parent.mkdir(parents=True, exist_ok=True)
    DISCOVERED_PATH.write_text(
        json.dumps({"updated_at": datetime.now(timezone.utc).isoformat(), "boards": current}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return new_boards


def discovery_input() -> dict[str, Any]:
    return {
        "queries": "\n".join(DISCOVERY_QUERIES),
        "maxPagesPerQuery": 2,
        "resultsPerPage": 10,
        "mobileResults": False,
        "languageCode": "en",
    }


def wellfound_input(max_items: int) -> dict[str, Any]:
    return {
        "startUrls": [
            {"url": "https://wellfound.com/role/l/software-engineer/romania"},
            {"url": "https://wellfound.com/role/r/software-engineer/europe"},
        ],
        "maxItems": max(1, max_items),
    }


def estimated_discovery_cost() -> float:
    return DISCOVERY_COST_USD


def estimated_wellfound_cost(max_items: int) -> float:
    return max_items * WELLFOUND_COST_PER_ROW + 0.001


def wellfound_max_items(state: ApifyState | None = None) -> int:
    state = state or ApifyState.load()
    remaining = state.remaining_budget()
    if remaining <= 0:
        return 0
    return max(0, min(40, int(remaining / WELLFOUND_COST_PER_ROW)))


def run_discovery(*, dry_run: bool = False, client: ApifyClient | None = None, check_cooldown: bool = True) -> list[dict[str, str]]:
    payload = discovery_input()
    cost = estimated_discovery_cost()
    if dry_run:
        print(f"· discover dry-run  actor={apify_actor_discovery()}  cost≈${cost:.3f}")
        print(f"  queries={len(DISCOVERY_QUERIES)}  pages/query=2")
        return []
    items = guarded_run(
        apify_actor_discovery(),
        payload,
        estimated_cost_usd=cost,
        limit=200,
        client=client,
        check_cooldown=check_cooldown,
    )
    boards = boards_from_serp(items)
    new_boards = merge_discovered(boards)
    print(f"· discover: {len(boards)} boards extracted, {len(new_boards)} new → {DISCOVERED_PATH}")
    return new_boards


def _cache_payload(items: list[dict[str, Any]], query_id: str) -> dict[str, Any]:
    existing = _load_json(APIFY_CACHE_PATH, {"items": []})
    if not isinstance(existing, dict):
        existing = {"items": []}
    previous = [x for x in (existing.get("items") or []) if isinstance(x, dict) and x.get("query_id") != query_id]
    stamped = []
    for item in items:
        row = dict(item)
        row["query_id"] = query_id
        stamped.append(row)
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "items": previous + stamped,
    }


def run_wellfound(
    *,
    dry_run: bool = False,
    client: ApifyClient | None = None,
    check_cooldown: bool = True,
) -> list[dict[str, Any]]:
    max_items = wellfound_max_items()
    cost = estimated_wellfound_cost(max_items) if max_items else 0.0
    payload = wellfound_input(max_items)
    if dry_run:
        print(f"· wellfound dry-run  actor={apify_actor_wellfound()}  maxItems={max_items}  cost≈${cost:.3f}")
        return []
    if max_items <= 0:
        print("· wellfound: no remaining budget, skipping")
        return []
    items = guarded_run(
        apify_actor_wellfound(),
        payload,
        estimated_cost_usd=cost,
        limit=max_items,
        client=client,
        check_cooldown=check_cooldown,
    )
    cache = _cache_payload(items, "wellfound")
    APIFY_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    APIFY_CACHE_PATH.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")
    print(f"· wellfound: {len(items)} rows → {APIFY_CACHE_PATH}")
    return items


def load_queries() -> list[dict[str, Any]]:
    raw = _load_json(APIFY_QUERIES_PATH, {"queries": []})
    items = raw.get("queries") if isinstance(raw, dict) else raw
    return [q for q in (items or []) if isinstance(q, dict)]


def apify_refresh(*, dry_run: bool = False, force: bool = False) -> int:
    """CLI entry: discovery + Wellfound, no-op without APIFY_TOKEN."""
    client = ApifyClient()
    if not client.enabled and not dry_run:
        print("· apify-refresh: APIFY_TOKEN not set, nothing to do")
        return 0
    state = ApifyState.load()
    ok, reason = state.can_run(check_cooldown=not force)
    if not ok and not dry_run:
        print(f"· apify-refresh: skipping — {reason}")
        return 0
    print(
        f"· apify budget  month={state.month}  spent=${state.spent_usd:.2f}  "
        f"remaining=${state.remaining_budget():.2f}  runs={state.runs}"
    )
    run_discovery(dry_run=dry_run, client=client)
    # Same invocation: skip the 6h cooldown so Wellfound can run after discovery records last_run.
    run_wellfound(dry_run=dry_run, client=client, check_cooldown=False)
    return 0
