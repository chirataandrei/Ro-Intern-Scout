from __future__ import annotations

from internscout.http import HttpClient
from internscout.models import Job
from internscout.sources import uid

SEARCH_URL = (
    "https://nofluffjobs.com/api/search/posting"
    "?limit=50&offset=0&salaryCurrency=EUR&salaryPeriod=month"
)
CITIES = (
    "Bucharest",
    "Cluj-Napoca",
    "Iasi",
    "Timisoara",
)
KEYWORDS = ("internship", "intern")


def _places(raw: dict) -> str:
    loc = raw.get("location") or {}
    if not isinstance(loc, dict):
        return str(loc or "")
    bits: list[str] = []
    for place in loc.get("places") or []:
        if not isinstance(place, dict):
            continue
        country = place.get("country") or {}
        country_name = country.get("name") if isinstance(country, dict) else country
        bits.extend(
            str(x)
            for x in (place.get("city"), place.get("province"), country_name)
            if x
        )
    if loc.get("fullyRemote"):
        bits.append("Remote")
    return ", ".join(x for x in bits if x)


def jobs_from_postings(postings: list) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    for raw in postings:
        if not isinstance(raw, dict):
            continue
        job_id = str(raw.get("id") or "")
        if not job_id or job_id in seen:
            continue
        seen.add(job_id)
        jobs.append(
            Job(
                uid=uid("nofluffjobs", "nofluffjobs", job_id),
                company=str(raw.get("name") or "Unknown company"),
                category="aggregator",
                title=str(raw.get("title") or "").strip(),
                location=_places(raw) or "Romania",
                url=f"https://nofluffjobs.com/job/{job_id}",
                source="nofluffjobs",
            )
        )
    return jobs


def fetch_jobs(http: HttpClient) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    for city in CITIES:
        for keyword in KEYWORDS:
            status, data = http.post_json(
                SEARCH_URL,
                {"page": 1, "criteriaSearch": {"keyword": [keyword], "city": [city]}},
            )
            if status != 200 or not isinstance(data, dict):
                continue
            for job in jobs_from_postings(data.get("postings") or []):
                if job.uid in seen:
                    continue
                seen.add(job.uid)
                jobs.append(job)
    return jobs
