#!/usr/bin/env python3
"""Probe ATS endpoints for catalog candidates.

For every candidate in tools/candidates.json (and optionally the pending
tokens in data/discovered.json) we generate slug variants, hit the 17
public JSON ATS endpoints through the real fetchers in
internscout.sources.ats.registry.FETCHERS, and keep only boards that
return HTTP 200 with a parsable jobs payload.

A live board with zero current postings still counts — empty JSON is
valid; a 200 HTML parking page is not.

Usage:
    python3 tools/probe_ats.py
    python3 tools/probe_ats.py --write
    python3 tools/probe_ats.py --limit 20
    python3 tools/probe_ats.py --from-discovered --write
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from internscout.catalog.loader import VALID_CATEGORIES, load_companies  # noqa: E402
from internscout.catalog.naming import (  # noqa: E402
    _official_careers,
    board_public_url,
    canonical_name,
)
from internscout.config import COMPANIES_DIR, DISCOVERED_PATH, OFFICIAL_CAREERS_PATH  # noqa: E402
from internscout.filters import _fold  # noqa: E402
from internscout.models import Company  # noqa: E402
from internscout.net.http import HttpClient  # noqa: E402
from internscout.net.pool import make_shared_http_client, run_parallel, safe_print  # noqa: E402
from internscout.sources.ats.registry import FETCHERS  # noqa: E402

import threading

_progress_lock = threading.Lock()
_progress = [0, 0]  # done, hits

CANDIDATES_PATH = ROOT / "tools" / "candidates.json"
RESULTS_PATH = ROOT / "tools" / "probe_results.json"

PROBE_ATS = (
    "greenhouse",
    "lever",
    "ashby",
    "smartrecruiters",
    "workable",
    "recruitee",
    "teamtailor",
    "personio",
    "breezy",
    "pinpoint",
    "bamboohr",
    "join",
    "jazzhr",
    "freshteam",
    "jobsoid",
    "comeet",
    "rippling",
)

_LEGAL_SUFFIXES = {
    "capital", "group", "romania", "srl", "sa", "ltd", "limited", "inc",
    "gmbh", "ag", "nv", "bv", "plc", "holdings", "partners", "management",
    "investments", "investment", "trading", "technologies", "technology",
    "international", "europe", "uk", "llc", "corp", "corporation", "company",
    "co", "bank", "insurance", "consulting", "advisory", "asset",
    "development", "services", "solutions", "software", "systems", "labs",
    "lab", "studio", "studios", "interactive", "holdings", "the",
}

_WORD_RE = re.compile(r"[a-z0-9]+")
_TOKEN_RE = re.compile(r"[a-z0-9]{4,}")


def slug_variants(name: str, extra: list[str] | None = None) -> list[str]:
    """lowercase / no-spaces / hyphenated, plus variants without legal suffixes."""
    folded = _fold(name or "")
    words = _WORD_RE.findall(folded)
    stripped = [w for w in words if w not in _LEGAL_SUFFIXES]
    sequences = [words]
    if stripped and stripped != words:
        sequences.append(stripped)
    if extra:
        for item in extra:
            extra_words = _WORD_RE.findall(_fold(item))
            if extra_words:
                sequences.append(extra_words)

    out: list[str] = []
    seen: set[str] = set()

    def add(slug: str) -> None:
        slug = slug.strip("-")
        if len(slug) < 2 or slug in seen:
            return
        seen.add(slug)
        out.append(slug)

    for seq in sequences:
        if not seq:
            continue
        add("".join(seq))
        add("-".join(seq))
        if len(seq) > 1:
            if len(seq[0]) >= 5:
                add(seq[0])
            add("".join(seq[:2]))
            add("-".join(seq[:2]))
    for item in extra or []:
        add(_fold(item).replace(" ", "").replace(".", ""))
        add(_fold(item).replace(" ", "-"))
    return out


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(_fold(text or "")))


def names_compatible(candidate: str, board_name: str) -> bool:
    """Reject a 200 that clearly belongs to a different company.

    Initials and short slugs (cfm, mmc, ti) can collide with unrelated
    Greenhouse boards; we keep the board only when the payload name shares
    a meaningful token with the candidate, or one name contains the other.
    """
    if not board_name:
        return True
    cand = _fold(candidate)
    board = _fold(board_name)
    if cand in board or board in cand:
        return True
    cand_tokens = _tokens(candidate) - _LEGAL_SUFFIXES
    board_tokens = _tokens(board_name) - _LEGAL_SUFFIXES
    if cand_tokens and board_tokens and cand_tokens & board_tokens:
        return True
    # Single short token (n8n, cqs, bdo) — substring of either side is enough.
    if len(cand.replace(" ", "")) <= 4 and cand.replace(" ", "") in board.replace(" ", ""):
        return True
    return False


def _parseable(ats: str, status: int, data: Any, body: str = "") -> bool:
    if status != 200:
        return False
    if ats in {"greenhouse", "ashby", "workable", "recruitee", "teamtailor"}:
        return isinstance(data, dict) and any(
            key in data for key in ("jobs", "offers", "items", "data", "name")
        )
    if ats in {"lever", "breezy"}:
        return isinstance(data, list)
    if ats == "smartrecruiters":
        return isinstance(data, dict) and "content" in data
    if ats == "personio":
        return "<position" in (body or "").lower() or "personio" in (body or "").lower()
    if ats == "pinpoint":
        items = data.get("data") or data.get("jobs") or data.get("postings") if isinstance(data, dict) else data
        return isinstance(items, list) or isinstance(data, dict)
    if ats == "bamboohr":
        return data is not None
    if ats == "rippling":
        items = data.get("items") or data.get("jobs") or data.get("data") if isinstance(data, dict) else data
        return isinstance(items, list) or isinstance(data, dict)
    if ats == "jobsoid":
        items = data.get("jobs") or data.get("data") if isinstance(data, dict) else data
        return isinstance(items, list)
    if ats == "comeet":
        items = data.get("positions") or data.get("data") if isinstance(data, dict) else data
        return isinstance(items, list)
    if ats == "join":
        from internscout.sources.ats.join import company_id_from_html

        return bool(company_id_from_html(body or ""))
    if ats in {"jazzhr", "freshteam"}:
        return bool(body) and "html" in (body or "")[:200].lower()
    return False


def _probe_urls(ats: str, token: str) -> list[str]:
    return {
        "greenhouse": [f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"],
        "lever": [f"https://api.lever.co/v0/postings/{token}?mode=json"],
        "ashby": [f"https://api.ashbyhq.com/posting-api/job-board/{token}"],
        "smartrecruiters": [f"https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=10&offset=0"],
        "workable": [f"https://apply.workable.com/api/v1/widget/accounts/{token}?details=false"],
        "recruitee": [f"https://{token}.recruitee.com/api/offers/"],
        "teamtailor": [f"https://{token}.teamtailor.com/jobs.json"],
        "personio": [f"https://{token}.jobs.personio.com/xml", f"https://{token}.jobs.personio.de/xml"],
        "breezy": [f"https://{token}.breezy.hr/json"],
        "pinpoint": [f"https://{token}.pinpointhq.com/postings.json"],
        "bamboohr": [f"https://{token}.bamboohr.com/careers/list"],
        "join": [f"https://join.com/companies/{token}"],
        "jazzhr": [f"https://{token}.applytojob.com/"],
        "freshteam": [f"https://{token}.freshteam.com/jobs"],
        "jobsoid": [f"https://{token}.jobsoid.com/api/v1/jobs"],
        "comeet": [f"https://www.comeet.co/careers-api/2.0/company/{token}/positions?details=true"],
        "rippling": [
            f"https://api.rippling.com/platform/api/ats/v1/board/{token}/jobs",
            f"https://ats.rippling.com/api/v2/board/{token}/jobs?page=0&pageSize=10",
        ],
    }.get(ats, [])


def _payload_name(ats: str, data: Any, body: str = "") -> str:
    if isinstance(data, dict):
        for key in ("name", "companyName", "company_name", "title"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        company = data.get("company")
        if isinstance(company, dict):
            value = company.get("name") or company.get("title") or ""
            if value:
                return str(value)
    return ""


def probe_board(ats: str, token: str, candidate_name: str, category: str, http: HttpClient) -> dict[str, Any] | None:
    """Keep a board only when the real fetcher returns at least one parsable job.

    HTML 200 parking pages (JazzHR/Freshteam/Jobsoid) and empty JSON shells
    are rejected — they are why a naive status-code probe lights up false
    positives. Greenhouse hits additionally require the board's public name
    to be compatible with the candidate, so short slugs like ``ti`` / ``cfm``
    cannot attach a stranger's board.
    """
    if not token or ats not in FETCHERS:
        return None
    company = Company(name=candidate_name, category=category, ats=ats, token=token)
    try:
        jobs = FETCHERS[ats](company, http)
    except Exception:  # noqa: BLE001 — a crashing fetcher is not a valid board
        return None
    if not jobs:
        if ats == "greenhouse":
            status, data = http.get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}")
            if status == 200 and isinstance(data, dict):
                board_name = str(data.get("name") or "")
                if board_name and names_compatible(candidate_name, board_name):
                    return {
                        "ats": ats, "token": token, "host": "", "site": "",
                        "url": board_public_url(ats, token), "jobs": 0, "board_name": board_name,
                    }
            return None
        if ats == "lever":
            status, data = http.get_json(f"https://api.lever.co/v0/postings/{token}?mode=json")
            if status == 200 and isinstance(data, list):
                return {
                    "ats": ats, "token": token, "host": "", "site": "",
                    "url": board_public_url(ats, token), "jobs": 0, "board_name": "",
                }
            return None
        if ats == "ashby":
            status, data = http.get_json(f"https://api.ashbyhq.com/posting-api/job-board/{token}")
            if status == 200 and isinstance(data, dict) and "jobs" in data:
                return {
                    "ats": ats, "token": token, "host": "", "site": "",
                    "url": board_public_url(ats, token), "jobs": 0, "board_name": "",
                }
            return None
        return None
    board_name = ""
    if ats == "greenhouse":
        status, data = http.get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}")
        if status == 200 and isinstance(data, dict):
            board_name = str(data.get("name") or "")
        if board_name and not names_compatible(candidate_name, board_name):
            return None
    return {
        "ats": ats,
        "token": token,
        "host": "",
        "site": "",
        "url": board_public_url(ats, token),
        "jobs": len(jobs),
        "board_name": board_name,
    }


def existing_canonical_names() -> set[str]:
    return {canonical_name(c.name) for c in load_companies()}


def load_candidates(path: Path = CANDIDATES_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw.get("candidates") if isinstance(raw, dict) else raw
    return [item for item in (items or []) if isinstance(item, dict) and item.get("name")]


def load_discovered_candidates() -> list[dict[str, Any]]:
    if not DISCOVERED_PATH.exists():
        return []
    raw = json.loads(DISCOVERED_PATH.read_text(encoding="utf-8"))
    items = raw.get("boards") if isinstance(raw, dict) else raw
    out: list[dict[str, Any]] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        ats = str(item.get("ats") or "")
        token = str(item.get("token") or "")
        name = str(item.get("name") or token)
        if not ats or not token:
            continue
        out.append(
            {
                "name": name,
                "category": str(item.get("category") or "discovered"),
                "slugs": [token],
                "ats_hint": ats,
                "careers_url": str(item.get("careers_url") or ""),
                "discovered": True,
            }
        )
    return out


def _probe_pair(item: tuple[dict[str, Any], str], http: HttpClient) -> tuple[str, dict[str, Any] | None]:
    candidate, ats = item
    name = str(candidate["name"])
    category = str(candidate.get("category") or "other")
    hint = str(candidate.get("ats_hint") or "")
    hit = None
    if not (hint and ats != hint):
        slugs = slug_variants(name, list(candidate.get("slugs") or []))
        for slug in slugs:
            hit = probe_board(ats, slug, name, category, http)
            if hit:
                break
    with _progress_lock:
        _progress[0] += 1
        if hit:
            _progress[1] += 1
        done, hits = _progress
    if hit:
        safe_print(f"  hit {name:32} {hit['ats']:16} {hit['token']}  jobs={hit['jobs']}")
    elif done % 200 == 0:
        safe_print(f"  … {done} boards probed, {hits} live")
    return name, hit


def probe_candidates(
    candidates: list[dict[str, Any]],
    *,
    http: HttpClient | None = None,
    ats_filter: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    http = http or make_shared_http_client()
    existing = existing_canonical_names()
    kept: list[dict[str, Any]] = []
    skipped = 0
    for cand in candidates:
        name = str(cand["name"])
        if canonical_name(name) in existing and not cand.get("discovered"):
            safe_print(f"· skip duplicate  {name} → {canonical_name(name)}")
            skipped += 1
            continue
        kept.append(cand)
    ats_list = ats_filter or PROBE_ATS
    safe_print(f"· probing {len(kept)} candidates ({skipped} already in catalog), {len(ats_list)} ATS each")

    pairs = [(cand, ats) for cand in kept for ats in ats_list]
    hits = run_parallel(pairs, lambda pair: _probe_pair(pair, http))

    by_name: dict[str, dict[str, Any]] = {}
    for cand in kept:
        by_name[str(cand["name"])] = {
            "name": cand["name"],
            "category": cand.get("category") or "other",
            "careers_url": cand.get("careers_url") or "",
            "discovered": bool(cand.get("discovered")),
            "sites": [],
        }
    for (cand, ats), (name, hit) in zip(pairs, hits):
        if not hit:
            continue
        entry = by_name.get(name)
        if entry is None:
            continue
        if any(s["ats"] == hit["ats"] and s["token"] == hit["token"] for s in entry["sites"]):
            continue
        entry["sites"].append({k: hit[k] for k in ("ats", "token", "host", "site", "url")})
    return list(by_name.values())


def _company_row(result: dict[str, Any]) -> dict[str, Any]:
    sites = list(result.get("sites") or [])
    careers_url = str(result.get("careers_url") or "")
    if careers_url and not any(s.get("ats") == "careers" for s in sites):
        sites.append(
            {
                "ats": "careers",
                "token": result["name"],
                "host": careers_url,
                "site": "",
                "url": careers_url,
            }
        )
    if not sites:
        sites = [
            {
                "ats": "careers",
                "token": result["name"],
                "host": careers_url,
                "site": "",
                "url": careers_url,
            }
        ]
    primary = next((s for s in sites if s.get("ats") != "careers"), sites[0] if sites else {})
    urls = [str(s.get("url") or "") for s in sites if s.get("url")]
    row: dict[str, Any] = {
        "name": result["name"],
        "category": result.get("category") or "other",
        "ats": str(primary.get("ats") or "careers"),
        "token": str(primary.get("token") or ""),
        "host": str(primary.get("host") or ""),
        "site": str(primary.get("site") or ""),
        "sites": sites,
        "urls": urls,
    }
    if result.get("discovered"):
        row["discovered_at"] = datetime.now(timezone.utc).date().isoformat()
    return row


def _load_shard(category: str) -> list[dict[str, Any]]:
    path = COMPANIES_DIR / f"{category}.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("companies") if isinstance(data, dict) else data
    return list(items or [])


def _save_shard(category: str, rows: list[dict[str, Any]]) -> None:
    path = COMPANIES_DIR / f"{category}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(rows, key=lambda r: str(r.get("name") or "").lower())
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_results(results: list[dict[str, Any]]) -> tuple[int, int]:
    """Merge probed companies into catalog shards + official_careers.json."""
    added = 0
    careers_added = 0
    official = dict(_official_careers())
    existing = existing_canonical_names()

    by_cat: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        name = str(result["name"])
        category = str(result.get("category") or "other")
        if category not in VALID_CATEGORIES:
            category = "other"
        row = _company_row(result)
        urls = [u for u in (row.get("urls") or []) if str(u).startswith("http")]
        if not urls:
            continue
        row["urls"] = urls
        if canonical_name(name) in existing and not result.get("discovered"):
            continue
        by_cat.setdefault(category, []).append(row)
        careers_url = str(result.get("careers_url") or "")
        if careers_url:
            urls = list(official.get(name) or [])
            if careers_url not in urls:
                urls.append(careers_url)
                official[name] = urls
                careers_added += 1

    for category, new_rows in by_cat.items():
        current = _load_shard(category)
        by_name = {str(r.get("name") or ""): r for r in current}
        for row in new_rows:
            by_name[row["name"]] = row
            added += 1
            existing.add(canonical_name(row["name"]))
        _save_shard(category, list(by_name.values()))

    if careers_added:
        OFFICIAL_CAREERS_PATH.write_text(
            json.dumps(official, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        _official_careers.cache_clear()
    return added, careers_added


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe ATS boards for catalog candidates.")
    parser.add_argument("--write", action="store_true", help="Merge live boards into catalog shards")
    parser.add_argument("--limit", type=int, default=0, help="Probe only the first N candidates")
    parser.add_argument("--from-discovered", action="store_true", help="Probe data/discovered.json instead")
    parser.add_argument("--candidates", type=Path, default=CANDIDATES_PATH)
    parser.add_argument(
        "--ats",
        default="",
        help="Comma-separated ATS list to probe (default: all 17)",
    )
    args = parser.parse_args(argv)

    candidates = load_discovered_candidates() if args.from_discovered else load_candidates(args.candidates)
    if args.limit:
        candidates = candidates[: args.limit]
    if not candidates:
        print("No candidates to probe.")
        return 0

    ats_filter = tuple(a.strip() for a in args.ats.split(",") if a.strip()) or None
    results = probe_candidates(candidates, ats_filter=ats_filter)
    live = sum(1 for r in results if r.get("sites"))
    RESULTS_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nProbed {len(results)} companies · {live} with at least one live ATS board")
    print(f"Wrote {RESULTS_PATH}")

    if args.write:
        added, careers = write_results(results)
        print(f"Merged {added} companies into catalog shards · {careers} official careers URLs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
