from __future__ import annotations

import json
import re

from internscout.http import HttpClient
from internscout.models import Job
from internscout.sources import uid

LIST_URLS = [
    "https://www.ejobs.ro/locuri-de-munca/it-software/internship",
    "https://www.ejobs.ro/locuri-de-munca/internship",
    "https://www.ejobs.ro/locuri-de-munca/it-software",
]

NUXT_RE = re.compile(
    r'<script[^>]+id="__NUXT_DATA__"[^>]*>(.*?)</script>',
    re.I | re.S,
)
LD_RE = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
    re.I | re.S,
)
JOB_PATH_RE = re.compile(r"/user/locuri-de-munca/([^/]+)/(\d+)")
JOB_KEYS = {"id", "title", "company", "slug"}


def _at(data: list, ref: object) -> object:
    if isinstance(ref, bool) or ref is None or isinstance(ref, str):
        return ref
    if isinstance(ref, int):
        if ref < 0 or ref >= len(data):
            return ref
        val = data[ref]
        if isinstance(val, (str, bool)) or val is None:
            return val
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            return val
        return val
    return ref


def _city_map(data: list) -> dict[int, str]:
    mapping: dict[int, str] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        if "faecetType" not in item and "facetType" not in item:
            continue
        kind = _at(data, item.get("faecetType") or item.get("facetType"))
        if str(kind).lower() not in {"cities", "city"}:
            continue
        city_id = _at(data, item.get("id"))
        name = _at(data, item.get("name"))
        if isinstance(city_id, int) and isinstance(name, str) and name:
            mapping[city_id] = name
    return mapping


def _company_name(data: list, company_ref: object) -> str:
    obj = _at(data, company_ref)
    if isinstance(obj, str):
        return obj.strip()
    if isinstance(obj, dict) and "name" in obj:
        name = _at(data, obj["name"])
        if isinstance(name, str):
            return name.strip()
    return ""


def _location_names(data: list, loc_ref: object, cities: dict[int, str]) -> str:
    raw = _at(data, loc_ref)
    names: list[str] = []
    items = raw if isinstance(raw, list) else [raw]
    for item in items:
        loc = _at(data, item)
        if isinstance(loc, str) and loc.strip():
            names.append(loc.strip())
            continue
        if not isinstance(loc, dict):
            continue
        if "name" in loc:
            name = _at(data, loc["name"])
            if isinstance(name, str) and name.strip():
                names.append(name.strip())
                continue
        city_id = _at(data, loc.get("cityId"))
        if isinstance(city_id, int) and city_id in cities:
            names.append(cities[city_id])
    unique = list(dict.fromkeys(names))
    if unique:
        return ", ".join(unique) + ", Romania"
    return "Romania"


def jobs_from_nuxt(body: str) -> list[tuple[str, str, str, str, str]]:
    match = NUXT_RE.search(body)
    if not match:
        return []
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    cities = _city_map(data)
    found: list[tuple[str, str, str, str, str]] = []
    seen: set[str] = set()
    for item in data:
        if not isinstance(item, dict) or not JOB_KEYS <= set(item.keys()):
            continue
        job_id = str(_at(data, item["id"]) or "")
        title = str(_at(data, item["title"]) or "").strip()
        slug = str(_at(data, item["slug"]) or "").strip()
        if not job_id or not title or job_id in seen:
            continue
        seen.add(job_id)
        company = _company_name(data, item["company"])
        location = _location_names(data, item.get("locations"), cities)
        url = f"https://www.ejobs.ro/user/locuri-de-munca/{slug}/{job_id}" if slug else (
            f"https://www.ejobs.ro/user/locuri-de-munca/{job_id}"
        )
        found.append((job_id, title, company, location, url))
    return found


def _jobs_from_ld(blob: str) -> list[tuple[str, str, str]]:
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return []
    entity = data.get("mainEntity") if isinstance(data, dict) else None
    if not isinstance(entity, dict):
        return []
    out: list[tuple[str, str, str]] = []
    for el in entity.get("itemListElement") or []:
        if not isinstance(el, dict):
            continue
        item = el.get("item") if isinstance(el.get("item"), dict) else el
        title = str(item.get("name") or "")
        url = str(el.get("url") or item.get("id") or item.get("url") or "")
        if not title or not url:
            continue
        out.append((title, url, url.rstrip("/").split("/")[-1]))
    return out


def _company_from_job_page(http: HttpClient, url: str) -> tuple[str, str]:
    status, body = http.get(url, headers={"Accept": "text/html"})
    if status != 200:
        return "", ""
    for blob in LD_RE.findall(body):
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            continue
        nodes = data if isinstance(data, list) else [data]
        for node in nodes:
            if not isinstance(node, dict):
                continue
            org = node.get("hiringOrganization")
            loc = node.get("jobLocation")
            company = ""
            if isinstance(org, dict):
                company = str(org.get("name") or "").strip()
            locality = ""
            places = loc if isinstance(loc, list) else [loc]
            for place in places:
                if isinstance(place, dict):
                    addr = place.get("address") if isinstance(place.get("address"), dict) else {}
                    locality = str(addr.get("addressLocality") or "").strip()
                    if locality:
                        break
            if company:
                location = f"{locality}, Romania" if locality else "Romania"
                return company, location
    return "", ""


def fetch_jobs(http: HttpClient) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    for base in LIST_URLS:
        for page in range(1, 5):
            url = base if page == 1 else f"{base}?page={page}"
            status, body = http.get(url, headers={"Accept": "text/html"})
            if status != 200:
                break
            parsed = jobs_from_nuxt(body)
            if not parsed:
                found_ld: list[tuple[str, str, str]] = []
                for blob in LD_RE.findall(body):
                    found_ld.extend(_jobs_from_ld(blob))
                if not found_ld:
                    for path, job_id in JOB_PATH_RE.findall(body):
                        title = path.replace("-", " ")
                        found_ld.append(
                            (title, f"https://www.ejobs.ro/user/locuri-de-munca/{path}/{job_id}", job_id)
                        )
                parsed = [(job_id, title, "", "Romania", job_url) for title, job_url, job_id in found_ld]
            new = 0
            for job_id, title, company, location, job_url in parsed:
                if job_id in seen:
                    continue
                seen.add(job_id)
                new += 1
                apply_url = job_url if job_url.startswith("http") else f"https://www.ejobs.ro{job_url}"
                if not company:
                    page_company, page_loc = _company_from_job_page(http, apply_url)
                    company = page_company
                    if page_loc:
                        location = page_loc
                jobs.append(
                    Job(
                        uid=uid("ejobs", "ejobs", job_id),
                        company=company or "Unknown company",
                        category="aggregator",
                        title=title.strip(),
                        location=location or "Romania",
                        url=apply_url,
                        source="ejobs",
                    )
                )
            if new == 0:
                break
    return jobs
