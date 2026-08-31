"""Backward-compatible shim — email building/sending now lives in internscout.delivery.emailer."""

from __future__ import annotations

from internscout.delivery.emailer import (
    build_email,
    is_remote_eu_job,
    is_romania_job,
    send_email,
    split_for_email,
)

__all__ = [
    "build_email",
    "is_remote_eu_job",
    "is_romania_job",
    "send_email",
    "split_for_email",
]
