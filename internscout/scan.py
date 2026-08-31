"""Backward-compatible shim.

scan.py used to hold everything: .env loading, company loading, fetch,
filter, SMTP, CLI orchestration. It is now split into:

- internscout.config       — paths, .env loading, tunable thresholds
- internscout.catalog      — company catalog (sharded JSON + naming)
- internscout.pipeline     — scan(): fetch + filter + dedupe -> list[Job]
- internscout.runner       — run(): CLI-facing orchestration
- internscout.delivery.emailer — build_email / send_email

This module re-exports the same names so old imports keep working.
"""

from __future__ import annotations

import json
from pathlib import Path

from internscout.catalog.loader import load_companies as _load_companies
from internscout.config import load_dotenv
from internscout.delivery.emailer import build_email, is_romania_job, send_email
from internscout.models import Company
from internscout.pipeline import dedupe as _dedupe
from internscout.pipeline import scan
from internscout.runner import run


def load_companies(path: Path | None = None) -> list[Company]:
    if path is not None:
        raw = json.loads(path.read_text(encoding="utf-8"))
        items = raw.get("companies") if isinstance(raw, dict) else raw
        return [Company.from_dict(x) for x in items]
    return _load_companies()


__all__ = [
    "build_email",
    "is_romania_job",
    "load_companies",
    "load_dotenv",
    "run",
    "scan",
    "send_email",
]
