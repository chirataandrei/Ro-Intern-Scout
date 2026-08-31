"""Backward-compatible shim — the ATS registry now lives in sources/ats/registry.py."""

from __future__ import annotations

from internscout.sources.ats.registry import FETCHERS, fetch_company

__all__ = ["FETCHERS", "fetch_company"]
