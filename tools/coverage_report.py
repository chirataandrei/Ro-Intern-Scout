#!/usr/bin/env python3
"""Flag catalog companies that returned raw=0 on recent scans (blind spots)."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from internscout.config import APIFY_QUERIES_PATH, COVERAGE_PATH  # noqa: E402

BLIND_STREAK = 3


def main() -> int:
    if not COVERAGE_PATH.exists():
        print(f"No coverage file at {COVERAGE_PATH}")
        return 0
    payload = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
    companies = payload.get("companies") if isinstance(payload, dict) else payload
    blind = [row for row in (companies or []) if isinstance(row, dict) and int(row.get("raw") or 0) == 0]
    print(f"Coverage {payload.get('updated_at') if isinstance(payload, dict) else ''}")
    print(f"  companies: {len(companies or [])}  raw=0: {len(blind)}")
    for row in sorted(blind, key=lambda r: str(r.get("name") or ""))[:40]:
        print(f"  · {row.get('name')}  ({row.get('category')})")
    if len(blind) > 40:
        print(f"  … {len(blind) - 40} more")

    queries = {"queries": []}
    if APIFY_QUERIES_PATH.exists():
        queries = json.loads(APIFY_QUERIES_PATH.read_text(encoding="utf-8"))
    print(f"Apify queries file: {APIFY_QUERIES_PATH} ({len(queries.get('queries') or [])} entries)")
    print(f"(A company stays blind for {BLIND_STREAK} consecutive scans before we would enqueue website-content-crawler.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
