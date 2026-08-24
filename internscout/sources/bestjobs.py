from __future__ import annotations

import json
import re

from internscout.http import HttpClient
from internscout.models import Job
from internscout.sources import uid

LIST_URLS = [
    "https://www.bestjobs.eu/en/jobs/internship",
    "https://www.bestjobs.eu/en/jobs?keyword=internship%20IT",
    "https://www.bestjobs.eu/ro/locuri-de-munca/internship",
]

NEXT_RE = re.compile(
    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
    re.I | re.S,
)


def _cards_from_next(body: str) -> list[dict]:
    m = NEXT_RE.search(body)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []
    props = (data.get("props") or {}).get("pageProps") or {}
    cards = props.get("jobListCardsFromServer") or {}
    items = cards.get("items") if isinstance(cards, dict) else []
    return [x for x in items if isinstance(x, dict)] if isinstance(items, list) else []


def fetch_jobs(http: HttpClient) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    for base in LIST_URLS:
        for page in range(1, 5):
            url = base if page == 1 else (
                f"{base}&page={page}" if "?" in base else f"{base}?page={page}"
            )
            status, body = http.get(url, headers={"Accept": "text/html"})
            if status != 200:
                break
            items = _cards_from_next(body)
            new = 0
            for raw in items:
                job_id = str(raw.get("id") or raw.get("slug") or "")
                if not job_id or job_id in seen:
                    continue
                seen.add(job_id)
                new += 1
                locs = []
                for loc in raw.get("locations") or []:
                    if isinstance(loc, dict):
                        locs.append(str(loc.get("name") or ""))
                    else:
                        locs.append(str(loc))
                slug = str(raw.get("slug") or job_id)
                jobs.append(
                    Job(
                        uid=uid("bestjobs", "bestjobs", job_id),
                        company=str(raw.get("companyName") or "BestJobs"),
                        category="aggregator",
                        title=str(raw.get("title") or "").strip(),
                        location=", ".join(x for x in locs if x) or "Romania",
                        url=f"https://www.bestjobs.eu/en/job/{slug}",
                        source="bestjobs",
                    )
                )
            if new == 0:
                break
    return jobs
