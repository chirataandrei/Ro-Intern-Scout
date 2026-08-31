"""Backward-compatible shim — HttpClient now lives in internscout.net.http."""

from __future__ import annotations

from internscout.net.http import DEFAULT_TIMEOUT, REQUEST_GAP_SECONDS, USER_AGENT, HttpClient

__all__ = ["DEFAULT_TIMEOUT", "REQUEST_GAP_SECONDS", "USER_AGENT", "HttpClient"]
