from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from internscout.models import SEEN_PATH, Job


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


def split_new(jobs: list[Job], seen: set[str]) -> tuple[list[Job], list[Job]]:
    new, current = [], []
    for job in jobs:
        current.append(job)
        if job.uid not in seen:
            new.append(job)
    return new, current
