"""Thread pool over companies/feeds, sharing one HttpClient with a per-host
rate limiter (net.ratelimit.HostRateLimiter).

At ~990 companies, sequential fetching at REQUEST_GAP_SECONDS would take well
past the 45-minute workflow timeout. Different ATS hosts run concurrently
here; a single host is still capped at one request per gap.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, TypeVar

from internscout.config import http_max_workers, http_request_gap_seconds
from internscout.net.http import HttpClient
from internscout.net.ratelimit import HostRateLimiter

T = TypeVar("T")
R = TypeVar("R")

_print_lock = threading.Lock()


def safe_print(*args: object, **kwargs: object) -> None:
    with _print_lock:
        print(*args, **kwargs)  # noqa: T201 — this is the scan's console log


def make_shared_http_client() -> HttpClient:
    """One HttpClient safe to hand to every worker thread: gap=0 disables its
    own single-timeline throttle, replaced by the shared per-host limiter."""
    limiter = HostRateLimiter(gap=http_request_gap_seconds())
    return HttpClient(gap=0, host_limiter=limiter)


def run_parallel(
    items: list[T],
    fn: Callable[[T], R],
    *,
    max_workers: int | None = None,
) -> list[R]:
    """Runs fn(item) for every item, preserving input order in the result."""
    if not items:
        return []
    workers = max_workers or http_max_workers()
    results: list[R | None] = [None] * len(items)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fn, item): idx for idx, item in enumerate(items)}
        for future in futures:
            idx = futures[future]
            results[idx] = future.result()
    return results  # type: ignore[return-value]
