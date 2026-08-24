from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
COMPANIES_PATH = DATA_DIR / "companies.json"
SEEN_PATH = DATA_DIR / "seen.json"


@dataclass(frozen=True)
class Company:
    name: str
    category: str
    ats: str
    token: str = ""
    host: str = ""
    site: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Company:
        extra = dict(raw.get("extra") or {})
        return cls(
            name=str(raw["name"]),
            category=str(raw.get("category") or "other"),
            ats=str(raw["ats"]),
            token=str(raw.get("token") or ""),
            host=str(raw.get("host") or extra.get("host") or ""),
            site=str(raw.get("site") or extra.get("site") or ""),
            extra=extra,
        )


@dataclass
class Job:
    uid: str
    company: str
    category: str
    title: str
    location: str
    url: str
    source: str
    published: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
