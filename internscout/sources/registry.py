from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import amazon, apple, ashby, google, greenhouse, lever
from internscout.sources import meta, microsoft, recruitee, smartrecruiters
from internscout.sources import teamtailor, workday, workable

FETCHERS = {
    "greenhouse": greenhouse.fetch_jobs,
    "lever": lever.fetch_jobs,
    "ashby": ashby.fetch_jobs,
    "smartrecruiters": smartrecruiters.fetch_jobs,
    "workable": workable.fetch_jobs,
    "recruitee": recruitee.fetch_jobs,
    "teamtailor": teamtailor.fetch_jobs,
    "workday": workday.fetch_jobs,
    "amazon": amazon.fetch_jobs,
    "google": google.fetch_jobs,
    "microsoft": microsoft.fetch_jobs,
    "meta": meta.fetch_jobs,
    "apple": apple.fetch_jobs,
}


def fetch_company(company: Company, http: HttpClient) -> list[Job]:
    fn = FETCHERS.get(company.ats)
    if fn is None:
        return []
    return fn(company, http)
