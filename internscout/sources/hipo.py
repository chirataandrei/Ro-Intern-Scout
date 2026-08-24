from __future__ import annotations

import html as html_lib
import re
from urllib.parse import urljoin

from internscout.http import HttpClient
from internscout.models import Job
from internscout.sources import uid

LIST_URLS = [
    "https://www.hipo.ro/locuri-de-munca/cautajob/Internship",
    "https://www.hipo.ro/locuri-de-munca/cautajob/Toate-orasele/IT-Software",
    "https://www.hipo.ro/locuri-de-munca/cautajob/Toate-orasele/IT-Hardware",
    "https://www.hipo.ro/locuri-de-munca/cautajob/Internship/IT-Software",
]

HREF_RE = re.compile(r'href="(/locuri-de-munca/locuri_de_munca/(\d+)/[^"]+)"', re.I)
TITLE_RE = re.compile(r'class="job-title"[^>]*title="([^"]+)"', re.I)
H5_RE = re.compile(r"<h5[^>]*>(.*?)</h5>", re.S | re.I)
COMPANY_RE = re.compile(r'class="company-name"[^>]*>.*?<span>([^<]+)</span>', re.S | re.I)
IMG_ALT_RE = re.compile(r'<img[^>]+(?:alt|title)="([^"]+)"', re.I)
LOC_RE = re.compile(r"fa-map-marker-alt[^>]*>\s*</i>\s*([^<]+)", re.I)
TAG_RE = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    text = html_lib.unescape(TAG_RE.sub(" ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def _parse_listing(body: str) -> list[tuple[str, str, str, str, str]]:
    found: list[tuple[str, str, str, str, str]] = []
    seen_ids: set[str] = set()
    for href, job_id in HREF_RE.findall(body):
        if job_id in seen_ids:
            continue
        seen_ids.add(job_id)
        idx = body.find(href)
        window = body[max(0, idx - 800) : idx + 2000]
        title_m = TITLE_RE.search(window)
        h5_m = H5_RE.search(window)
        title = _clean((title_m.group(1) if title_m else "") or (h5_m.group(1) if h5_m else ""))
        if not title:
            title = _clean(href.rstrip("/").split("/")[-1].replace("-", " "))
        company_m = COMPANY_RE.search(window)
        img_m = IMG_ALT_RE.search(window)
        firm = _clean((company_m.group(1) if company_m else "") or (img_m.group(1) if img_m else ""))
        loc_m = LOC_RE.search(window)
        location = _clean(loc_m.group(1) if loc_m else "Romania")
        found.append((job_id, title, firm, location, href))
    return found


def fetch_jobs(http: HttpClient) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    for base in LIST_URLS:
        empty_pages = 0
        for n in range(1, 6):
            url = base if n == 1 else f"{base}/pagina-{n}"
            status, body = http.get(url, headers={"Accept": "text/html"})
            if status != 200:
                break
            parsed = _parse_listing(body)
            new_on_page = 0
            for job_id, title, firm, location, href in parsed:
                if job_id in seen:
                    continue
                seen.add(job_id)
                new_on_page += 1
                jobs.append(
                    Job(
                        uid=uid("hipo", "hipo", job_id),
                        company=firm or "Unknown company",
                        category="aggregator",
                        title=title,
                        location=location or "Romania",
                        url=urljoin("https://www.hipo.ro", href),
                        source="hipo",
                    )
                )
            if new_on_page == 0:
                empty_pages += 1
                if empty_pages >= 1:
                    break
    return jobs
