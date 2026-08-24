from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from internscout.career_sites import board_public_url, official_urls, site_key


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
COMPANIES_PATH = DATA_DIR / "companies.json"
SEEN_PATH = DATA_DIR / "seen.json"


def _board_from_fields(
    *,
    ats: str,
    token: str = "",
    host: str = "",
    site: str = "",
    extra: dict[str, Any] | None = None,
    url: str = "",
) -> dict[str, Any]:
    board = {
        "ats": ats,
        "token": token,
        "host": host,
        "site": site,
        "url": url or board_public_url(ats, token, host, site),
    }
    if extra:
        board["extra"] = extra
    return board


@dataclass(frozen=True)
class Company:
    name: str
    category: str
    ats: str
    token: str = ""
    host: str = ""
    site: str = ""
    extra: dict[str, Any] = field(default_factory=dict)
    sites: tuple[dict[str, Any], ...] = ()

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Company:
        extra = dict(raw.get("extra") or {})
        ats = str(raw.get("ats") or "")
        token = str(raw.get("token") or "")
        host = str(raw.get("host") or extra.get("host") or "")
        site = str(raw.get("site") or extra.get("site") or "")
        boards: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str, str]] = set()
        raw_sites = raw.get("sites")
        if isinstance(raw_sites, list) and raw_sites:
            for item in raw_sites:
                if not isinstance(item, dict) or not item.get("ats"):
                    continue
                board = _board_from_fields(
                    ats=str(item.get("ats") or ""),
                    token=str(item.get("token") or ""),
                    host=str(item.get("host") or ""),
                    site=str(item.get("site") or ""),
                    extra=dict(item.get("extra") or {}) or None,
                    url=str(item.get("url") or ""),
                )
                key = site_key(board)
                if key in seen:
                    continue
                seen.add(key)
                boards.append(board)
        if not boards and ats:
            boards.append(_board_from_fields(ats=ats, token=token, host=host, site=site, extra=extra or None))
            seen.add(site_key(boards[0]))
        for career_url in official_urls(str(raw.get("name") or "")):
            board = _board_from_fields(
                ats="careers",
                token=str(raw.get("name") or "careers"),
                host=career_url,
                url=career_url,
            )
            key = site_key(board)
            if key in seen or any(str(b.get("url") or "") == career_url for b in boards):
                continue
            seen.add(key)
            boards.append(board)
        primary = boards[0] if boards else _board_from_fields(ats=ats, token=token, host=host, site=site)
        return cls(
            name=str(raw["name"]),
            category=str(raw.get("category") or "other"),
            ats=str(primary.get("ats") or ats),
            token=str(primary.get("token") or token),
            host=str(primary.get("host") or host),
            site=str(primary.get("site") or site),
            extra=extra,
            sites=tuple(boards),
        )

    def boards(self) -> list["Company"]:
        raw_boards = self.sites or (
            _board_from_fields(
                ats=self.ats, token=self.token, host=self.host, site=self.site, extra=self.extra or None
            ),
        )
        expanded: list[Company] = []
        for board in raw_boards:
            extra = dict(self.extra)
            extra.update(board.get("extra") or {})
            expanded.append(
                Company(
                    name=self.name,
                    category=self.category,
                    ats=str(board.get("ats") or self.ats),
                    token=str(board.get("token") or self.token),
                    host=str(board.get("host") or self.host),
                    site=str(board.get("site") or self.site),
                    extra=extra,
                    sites=(),
                )
            )
        fetchable = [board for board in expanded if board.ats != "careers"]
        return fetchable or expanded


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
