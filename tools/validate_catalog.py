#!/usr/bin/env python3
"""Sanity-check the sharded catalog: names, categories, ATS, non-empty sites."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from internscout.catalog.loader import VALID_CATEGORIES, load_companies  # noqa: E402
from internscout.catalog.naming import canonical_name  # noqa: E402
from internscout.sources.ats.registry import FETCHERS  # noqa: E402


def main() -> int:
    companies = load_companies()
    errors: list[str] = []
    names: Counter[str] = Counter()
    for company in companies:
        key = canonical_name(company.name)
        names[key] += 1
        if company.category not in VALID_CATEGORIES:
            errors.append(f"{company.name}: bad category {company.category!r}")
        if not company.sites:
            errors.append(f"{company.name}: empty sites")
        for board in company.sites:
            ats = str(board.get("ats") or "")
            if ats and ats not in FETCHERS:
                errors.append(f"{company.name}: unknown ats {ats!r}")
    dupes = [name for name, n in names.items() if n > 1]
    for name in dupes:
        errors.append(f"duplicate canonical_name: {name}")
    print(f"Companies: {len(companies)}")
    if errors:
        print(f"FAIL ({len(errors)} issues)")
        for err in errors[:50]:
            print(f"  · {err}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
