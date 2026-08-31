from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Company, Job
from internscout.sources.ats import careers


def fetch_jobs(company: Company, http: HttpClient) -> list[Job]:
    """Public SuccessFactors boards often expose JobPosting JSON-LD on the career site."""
    jobs = careers.fetch_jobs(company, http)
    for job in jobs:
        job.source = "successfactors"
        job.uid = job.uid.replace("careers:", "successfactors:", 1)
    return jobs
