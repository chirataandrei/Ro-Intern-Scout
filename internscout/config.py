"""Paths, .env loading, and tunable thresholds.

Everything path- or environment-related lives here so that internscout.models
only has to describe the Company/Job domain, not where things are on disk.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

CATALOG_DIR = PACKAGE_DIR / "catalog" / "data"
COMPANIES_DIR = CATALOG_DIR / "companies"
ALIASES_PATH = CATALOG_DIR / "aliases.json"
OFFICIAL_CAREERS_PATH = CATALOG_DIR / "official_careers.json"

# Legacy single-file catalog. No longer written to, but load_companies()
# still merges it in for backward compatibility if it happens to exist.
COMPANIES_PATH = DATA_DIR / "companies.json"

SEEN_PATH = DATA_DIR / "seen.json"
COVERAGE_PATH = DATA_DIR / "coverage.json"

APIFY_CACHE_PATH = DATA_DIR / "apify_cache.json"
APIFY_STATE_PATH = DATA_DIR / "apify_state.json"
APIFY_QUERIES_PATH = DATA_DIR / "apify_queries.json"
DISCOVERED_PATH = DATA_DIR / "discovered.json"

ENV_PATH = ROOT / ".env"


def load_dotenv(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


# Load once at import time so any module that reads os.environ (directly or
# through the helpers below) sees .env values regardless of import order —
# config.py is transitively imported by almost everything before main logic
# runs. setdefault() means real environment variables still win.
load_dotenv()


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, "") or default)
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "") or default)
    except (TypeError, ValueError):
        return default


def apify_token() -> str:
    return (os.environ.get("APIFY_TOKEN") or "").strip()


def apify_max_spend_per_month() -> float:
    return _env_float("APIFY_MAX_SPEND_PER_MONTH", 4.20)


def apify_max_runs_per_month() -> int:
    return _env_int("APIFY_MAX_RUNS_PER_MONTH", 90)


def apify_min_hours_between_runs() -> float:
    return _env_float("APIFY_MIN_HOURS_BETWEEN_RUNS", 6.0)


def apify_actor_discovery() -> str:
    return os.environ.get("APIFY_ACTOR_DISCOVERY") or "apify/google-search-scraper"


def apify_actor_wellfound() -> str:
    return os.environ.get("APIFY_ACTOR_WELLFOUND") or "memo23/wellfound-jobs-scraper"


def http_max_workers() -> int:
    return _env_int("INTERNSCOUT_MAX_WORKERS", 8)


def http_request_gap_seconds() -> float:
    return _env_float("INTERNSCOUT_REQUEST_GAP_SECONDS", 0.35)
