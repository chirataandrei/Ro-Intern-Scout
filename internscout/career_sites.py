"""Backward-compatible shim.

The ALIASES / OFFICIAL_CAREERS data and the naming helpers now live in
``internscout.catalog.naming`` (data-only JSON files under
``internscout/catalog/data/``). This module re-exports the same names so
existing imports (``from internscout.career_sites import ...``) keep working.
"""

from __future__ import annotations

from internscout.catalog.naming import (
    ALIASES,
    OFFICIAL_CAREERS,
    board_public_url,
    canonical_name,
    official_urls,
    site_key,
)

__all__ = [
    "ALIASES",
    "OFFICIAL_CAREERS",
    "board_public_url",
    "canonical_name",
    "official_urls",
    "site_key",
]
