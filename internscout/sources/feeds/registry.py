from __future__ import annotations

from internscout.sources.base import FeedSpec
from internscout.sources.feeds import (
    apify_scout,
    arbeitnow,
    bestjobs,
    ejobs,
    himalayas,
    hipo,
    jobicy,
    juniors,
    landingjobs,
    nofluffjobs,
    remoteok,
    simplify,
    stagiipebune,
    undelucram,
    weworkremotely,
)

# Romanian aggregators: missing city safely defaults to Romania.
FEEDS: list[FeedSpec] = [
    FeedSpec("Hipo", "hipo", hipo.fetch_jobs),
    FeedSpec("eJobs", "ejobs", ejobs.fetch_jobs),
    FeedSpec("BestJobs", "bestjobs", bestjobs.fetch_jobs),
    FeedSpec("Stagii pe Bune", "stagiipebune", stagiipebune.fetch_jobs, already_romania=True, assume_internship=True),
    FeedSpec("Undelucram", "undelucram", undelucram.fetch_jobs, already_romania=True),
    FeedSpec("Juniors.ro", "juniors", juniors.fetch_jobs, already_romania=True),
    FeedSpec("NoFluffJobs", "nofluffjobs", nofluffjobs.fetch_jobs),
    # International: locations are real, so "no city" must never default to RO.
    FeedSpec("Simplify", "simplify", simplify.fetch_jobs, from_aggregator=False),
    FeedSpec("Arbeitnow (EU)", "arbeitnow", arbeitnow.fetch_jobs, from_aggregator=False),
    FeedSpec("RemoteOK", "remoteok", remoteok.fetch_jobs, from_aggregator=False),
    FeedSpec("Himalayas", "himalayas", himalayas.fetch_jobs, from_aggregator=False),
    FeedSpec("Jobicy (Europe)", "jobicy", jobicy.fetch_jobs, from_aggregator=False),
    FeedSpec("We Work Remotely", "weworkremotely", weworkremotely.fetch_jobs, from_aggregator=False),
    FeedSpec("Landing.jobs", "landingjobs", landingjobs.fetch_jobs, from_aggregator=False),
    FeedSpec("Apify (blind spots)", "apify", apify_scout.fetch_jobs, from_aggregator=False),
]
