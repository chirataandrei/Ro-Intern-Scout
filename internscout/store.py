from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from internscout.catalog.naming import canonical_name
from internscout.config import SEEN_PATH
from internscout.filters import _fold
from internscout.models import Job

_WORD_RE = re.compile(r"[a-z0-9]+")

# English vs Romanian city spellings that _fold's diacritics-stripping alone
# does not collapse (different words, not just different accents).
_CITY_ALIASES = {
    "bucharest": "bucuresti",
    "cluj napoca": "cluj",
    "jassy": "iasi",
    "hermannstadt": "sibiu",
    "kronstadt": "brasov",
    "temeswar": "timisoara",
}


def load_seen(path: Path = SEEN_PATH) -> set[str]:
    if not path.exists():
        return set()
    raw = json.loads(path.read_text(encoding="utf-8"))
    ids = raw.get("ids") if isinstance(raw, dict) else raw
    if not isinstance(ids, list):
        return set()
    return {str(x) for x in ids}


def save_seen(ids: set[str], path: Path = SEEN_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "ids": sorted(ids),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _norm(text: str) -> str:
    return " ".join(_WORD_RE.findall(_fold(text or "")))


def _norm_city(location: str) -> str:
    # Only the first comma-separated segment (almost always the city) so
    # "Bucharest, Romania" and "București, România" collapse to the same key.
    first_segment = _fold(location or "").split(",")[0]
    words = " ".join(_WORD_RE.findall(first_segment))
    return _CITY_ALIASES.get(words, words)


def fingerprint(job: Job) -> str:
    """Cross-source identity: same company + same role + same city.

    Lets the same posting seen both directly on an ATS board and through an
    aggregator/Apify (Wellfound, LinkedIn) collapse into a single "NEW" card
    instead of two.
    """
    blob = f"{canonical_name(job.company)}|{_norm(job.title)}|{_norm_city(job.location)}"
    return "fp:" + hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


def seen_keys_for(jobs: list[Job]) -> set[str]:
    keys: set[str] = set()
    for job in jobs:
        keys.add(job.uid)
        keys.add(fingerprint(job))
    return keys


def split_new(jobs: list[Job], seen: set[str]) -> tuple[list[Job], list[Job]]:
    new, current = [], []
    for job in jobs:
        current.append(job)
        if job.uid not in seen and fingerprint(job) not in seen:
            new.append(job)
    return new, current
