"""Canonical company names, alias resolution, and ATS board URL building.

ALIASES and OFFICIAL_CAREERS used to be hardcoded dicts in career_sites.py.
They now live in catalog/data/*.json so that adding a firm's official
careers URL or an alias correction is a data-only diff.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

from internscout.config import ALIASES_PATH, OFFICIAL_CAREERS_PATH

# ATS suffixes used when the same firm was entered twice with another board.
_ATS_SUFFIX = re.compile(
    r"\s+(Workable|Recruitee|Greenhouse|Ashby|Lever|SmartRecruiters|"
    r"Personio|Breezy|Pinpoint|BambooHR|Eightfold|iCIMS|Join|Rippling|"
    r"JazzHR|Freshteam|Softgarden|Teamtailor|Jobsoid|Careers|Jobs)$",
    re.I,
)


@lru_cache(maxsize=1)
def _aliases() -> dict[str, str]:
    if not ALIASES_PATH.exists():
        return {}
    return json.loads(ALIASES_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _official_careers() -> dict[str, list[str]]:
    if not OFFICIAL_CAREERS_PATH.exists():
        return {}
    return json.loads(OFFICIAL_CAREERS_PATH.read_text(encoding="utf-8"))


# Backward-compatible module-level dicts (career_sites.py used to expose
# these directly). Frozen at import time; tests / tools that only read them
# still work.
ALIASES: dict[str, str] = _aliases()
OFFICIAL_CAREERS: dict[str, list[str]] = _official_careers()


def canonical_name(name: str) -> str:
    aliases = _aliases()
    if name in aliases:
        return aliases[name]
    cleaned = name.strip()
    while True:
        nxt = _ATS_SUFFIX.sub("", cleaned).strip()
        if nxt == cleaned:
            break
        cleaned = nxt
    return aliases.get(cleaned, cleaned)


def board_public_url(ats: str, token: str = "", host: str = "", site: str = "") -> str:
    token = (token or "").strip()
    host = (host or "").strip().rstrip("/")
    site = (site or "").strip().strip("/")
    if host.startswith("http://") or host.startswith("https://"):
        return host
    mapping = {
        "greenhouse": f"https://job-boards.greenhouse.io/{token}",
        "lever": f"https://jobs.lever.co/{token}",
        "ashby": f"https://jobs.ashbyhq.com/{token}",
        "smartrecruiters": f"https://careers.smartrecruiters.com/{token}",
        "workable": f"https://apply.workable.com/{token}/",
        "recruitee": f"https://{token}.recruitee.com/",
        "teamtailor": f"https://{token}.teamtailor.com/jobs",
        "personio": f"https://{token}.jobs.personio.com/",
        "breezy": f"https://{token}.breezy.hr/",
        "pinpoint": f"https://{token}.pinpointhq.com/",
        "bamboohr": f"https://{token}.bamboohr.com/careers",
        "google": "https://www.google.com/about/careers/applications/jobs/results/",
        "amazon": "https://www.amazon.jobs/",
        "microsoft": "https://jobs.careers.microsoft.com/",
        "meta": "https://www.metacareers.com/",
        "apple": "https://jobs.apple.com/",
        "comeet": f"https://www.comeet.com/jobs/{token}",
        "successfactors": host or "",
        "careers": host or "",
        "eightfold": f"https://{host}/careers" if host else "",
        "icims": f"https://{host}/jobs/search" if host else "",
        "join": f"https://join.com/companies/{token}",
        "rippling": f"https://ats.rippling.com/{token}/jobs",
        "jazzhr": f"https://{token}.applytojob.com/",
        "freshteam": f"https://{token}.freshteam.com/jobs",
        "jobsoid": f"https://{token}.jobsoid.com/",
        "softgarden": host or (f"https://{token}.jobs.softgarden.io/" if token else ""),
        "workday": f"https://{host}/{site}" if host and site else (f"https://{host}" if host else ""),
    }
    return mapping.get(ats, "") or ""


def official_urls(name: str) -> list[str]:
    return list(_official_careers().get(canonical_name(name), []))


def site_key(site: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(site.get("ats") or ""),
        str(site.get("token") or ""),
        str(site.get("host") or ""),
        str(site.get("site") or ""),
    )
