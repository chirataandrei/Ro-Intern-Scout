from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources import amazon, apple, ashby, bamboohr, breezy, careers, comeet
from internscout.sources import eightfold, freshteam, google, greenhouse, icims, jazzhr, join
from internscout.sources import lever, meta, microsoft, personio, pinpoint, recruitee, rippling
from internscout.sources import smartrecruiters, softgarden, successfactors, teamtailor, workday
from internscout.sources import workable

FETCHERS = {
    "greenhouse": greenhouse.fetch_jobs,
    "lever": lever.fetch_jobs,
    "ashby": ashby.fetch_jobs,
    "smartrecruiters": smartrecruiters.fetch_jobs,
    "workable": workable.fetch_jobs,
    "recruitee": recruitee.fetch_jobs,
    "teamtailor": teamtailor.fetch_jobs,
    "workday": workday.fetch_jobs,
    "personio": personio.fetch_jobs,
    "breezy": breezy.fetch_jobs,
    "pinpoint": pinpoint.fetch_jobs,
    "bamboohr": bamboohr.fetch_jobs,
    "eightfold": eightfold.fetch_jobs,
    "comeet": comeet.fetch_jobs,
    "icims": icims.fetch_jobs,
    "successfactors": successfactors.fetch_jobs,
    "join": join.fetch_jobs,
    "rippling": rippling.fetch_jobs,
    "jazzhr": jazzhr.fetch_jobs,
    "freshteam": freshteam.fetch_jobs,
    "softgarden": softgarden.fetch_jobs,
    "careers": careers.fetch_jobs,
    "amazon": amazon.fetch_jobs,
    "google": google.fetch_jobs,
    "microsoft": microsoft.fetch_jobs,
    "meta": meta.fetch_jobs,
    "apple": apple.fetch_jobs,
}


def fetch_company(company: Company, http: HttpClient) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    for board in company.boards():
        fn = FETCHERS.get(board.ats)
        if fn is None:
            continue
        for job in fn(board, http):
            if job.uid in seen:
                continue
            seen.add(job.uid)
            jobs.append(job)
    return jobs
