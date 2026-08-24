from __future__ import annotations

import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

from internscout.emailer import build_email, is_romania_job
from internscout.filters import keep_job
from internscout.http import HttpClient
from internscout.models import COMPANIES_PATH, Company, Job, SEEN_PATH
from internscout.sources import bestjobs, ejobs, hipo, simplify, stagiipebune
from internscout.sources.registry import fetch_company
from internscout.store import load_seen, save_seen, split_new


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_companies(path: Path = COMPANIES_PATH) -> list[Company]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw.get("companies") if isinstance(raw, dict) else raw
    return [Company.from_dict(x) for x in items]


def _dedupe(jobs: list[Job]) -> list[Job]:
    seen: set[str] = set()
    out: list[Job] = []
    for job in jobs:
        key = job.uid
        if key in seen:
            continue
        seen.add(key)
        out.append(job)
    return out


def scan(http: HttpClient | None = None) -> list[Job]:
    http = http or HttpClient()
    collected: list[Job] = []
    for company in load_companies():
        try:
            raw_jobs = fetch_company(company, http)
        except Exception as exc:  # noqa: BLE001
            print(f"! {company.name} ({company.ats}): {exc}")
            continue
        kept = 0
        for job in raw_jobs:
            if keep_job(
                title=job.title,
                location=job.location,
                extra=f"{job.url} {job.company}",
                category=job.category,
                company=job.company,
                from_aggregator=False,
            ):
                collected.append(job)
                kept += 1
        print(f"· {company.name:28} sites={len(company.sites):2} raw={len(raw_jobs):4} kept={kept:3}")

    aggregators = [
        ("Hipo", "hipo", hipo.fetch_jobs, False, False),
        ("eJobs", "ejobs", ejobs.fetch_jobs, False, False),
        ("BestJobs", "bestjobs", bestjobs.fetch_jobs, False, False),
        ("Stagii pe Bune", "stagiipebune", stagiipebune.fetch_jobs, True, True),
        ("Simplify", "simplify", simplify.fetch_jobs, False, False),
    ]
    for label, source, fetch, already_ro, assume_intern in aggregators:
        try:
            raw_jobs = fetch(http)
        except Exception as exc:  # noqa: BLE001
            print(f"! {label}: {exc}")
            raw_jobs = []
        kept = 0
        for job in raw_jobs:
            if keep_job(
                title=job.title,
                location=job.location,
                extra=job.company,
                category=job.category,
                company=job.company,
                from_aggregator=source != "simplify",
                already_romania=already_ro,
                assume_internship=assume_intern,
            ):
                collected.append(job)
                kept += 1
        print(f"· {label:28} {source:16} raw={len(raw_jobs):4} kept={kept:3}")

    collected.sort(
        key=lambda j: (0 if is_romania_job(j) else 1, j.company.lower(), j.title.lower())
    )
    return _dedupe(collected)


def send_email(subject: str, plain: str, html_body: str) -> None:
    host = os.environ.get("SMTP_HOST") or "smtp.gmail.com"
    port = int(os.environ.get("SMTP_PORT") or "587")
    user = (os.environ.get("SMTP_USER") or "").strip()
    password = (os.environ.get("SMTP_PASS") or "").replace(" ", "").strip()
    to_addr = (os.environ.get("EMAIL_TO") or "").strip()
    from_addr = (os.environ.get("EMAIL_FROM") or user).strip() or user
    if not (user and password and to_addr):
        raise SystemExit("Set SMTP_USER, SMTP_PASS, and EMAIL_TO (see .env.example).")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(plain)
    msg.add_alternative(html_body, subtype="html")

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls(context=context)
        smtp.login(user, password)
        smtp.send_message(msg)


def run(*, send: bool, persist: bool) -> int:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    jobs = scan()
    seen = load_seen()
    new_jobs, open_jobs = split_new(jobs, seen)
    romania_n = sum(1 for job in open_jobs if is_romania_job(job))
    print(f"\nOpen: {len(open_jobs)}   New: {len(new_jobs)}   Romania: {romania_n}   Spring weeks: {len(open_jobs) - romania_n}")
    new_ids = {job.uid for job in new_jobs}
    for job in open_jobs[:100]:
        flag = "NEW" if job.uid in new_ids else "   "
        print(f"  [{flag}] {job.company} — {job.title} ({job.location})")
        print(f"         {job.url}")

    subject, plain, html_body = build_email(new_jobs, open_jobs)
    if send:
        send_email(subject, plain, html_body)
        print(f"Email sent: {subject}")
    if persist:
        save_seen(seen | {j.uid for j in open_jobs}, SEEN_PATH)
        print(f"Saved {SEEN_PATH} ({len(seen | {j.uid for j in open_jobs})} ids)")
    return 0
