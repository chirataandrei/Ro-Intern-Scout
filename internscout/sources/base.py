"""Shared shape for feed-style sources (aggregators, free job boards, Apify).

Every entry in sources.feeds.registry.FEEDS is a FeedSpec. pipeline.py just
iterates the list — adding a new feed becomes a data change instead of an
edit to the scan loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from internscout.http import HttpClient
from internscout.models import Job


@dataclass(frozen=True)
class FeedSpec:
    label: str
    source: str
    fetch: Callable[[HttpClient], list[Job]]
    already_romania: bool = False
    assume_internship: bool = False
    # False for boards that are not Romania-specific (Simplify, the free EU
    # feeds, Apify/Wellfound): keep_job must not assume "no city == Romania"
    # for them the way it safely can for Hipo/eJobs/BestJobs.
    from_aggregator: bool = True
