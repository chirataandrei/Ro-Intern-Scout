from __future__ import annotations

import html
import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from internscout.filters import is_remote_eu, is_romania, is_spring_week
from internscout.models import Job


def _esc(text: str) -> str:
    return html.escape(text or "", quote=True)


def is_romania_job(job: Job) -> bool:
    if is_romania(job.location, f"{job.company} {job.url}"):
        return True
    return job.source in {
        "hipo",
        "ejobs",
        "bestjobs",
        "stagiipebune",
        "undelucram",
        "juniors",
    } and not is_spring_week(job.title)


def is_remote_eu_job(job: Job) -> bool:
    if is_romania_job(job):
        return False
    if is_spring_week(job.title):
        return False
    return is_remote_eu(job.location, f"{job.company} {job.url}")


def split_for_email(jobs: list[Job]) -> tuple[list[Job], list[Job], list[Job]]:
    romania: list[Job] = []
    remote_eu: list[Job] = []
    spring: list[Job] = []
    for job in jobs:
        if is_romania_job(job):
            romania.append(job)
        elif is_remote_eu_job(job):
            remote_eu.append(job)
        else:
            spring.append(job)
    key = lambda j: (j.company.lower(), j.title.lower())
    romania.sort(key=key)
    remote_eu.sort(key=key)
    spring.sort(key=key)
    return romania, remote_eu, spring


def _card_html(job: Job, is_new: bool) -> str:
    badge = (
        "<span style='display:inline-block;background:#dcfce7;color:#166534;"
        "font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;"
        "margin-left:8px;vertical-align:middle'>NEW</span>"
        if is_new
        else ""
    )
    return f"""
    <div style="border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px;margin:0 0 10px">
      <div style="font-size:17px;font-weight:700;color:#0f172a">
        {_esc(job.company)}{badge}
      </div>
      <div style="font-size:15px;color:#1e293b;margin-top:6px">{_esc(job.title)}</div>
      <div style="color:#475569;font-size:13px;margin-top:4px">{_esc(job.location)}</div>
      <div style="margin-top:8px;font-size:13px">
        Apply:
        <a href="{_esc(job.url)}" style="color:#1d4ed8;word-break:break-all">{_esc(job.url)}</a>
      </div>
    </div>
    """


def _section_html(title: str, jobs: list[Job], new_ids: set[str], empty: str) -> str:
    heading = (
        f"<h2 style='font-size:16px;margin:28px 0 10px;color:#0f172a'>{_esc(title)}</h2>"
    )
    if not jobs:
        return heading + f"<p style='margin:0 0 16px;color:#64748b'>{_esc(empty)}</p>"
    return heading + "".join(_card_html(job, job.uid in new_ids) for job in jobs)


def _plain_section(title: str, jobs: list[Job], new_ids: set[str], empty: str) -> list[str]:
    lines = [title, ""]
    if not jobs:
        lines.append(empty)
        lines.append("")
        return lines
    for job in jobs:
        flag = "NEW  " if job.uid in new_ids else "     "
        lines.append(f"{flag}Company:  {job.company}")
        lines.append(f"     Title:    {job.title}")
        lines.append(f"     Location: {job.location}")
        lines.append(f"     Apply:    {job.url}")
        lines.append("")
    return lines


def build_email(new_jobs: list[Job], open_jobs: list[Job]) -> tuple[str, str, str]:
    today = datetime.now(ZoneInfo("Europe/Bucharest")).strftime("%d.%m.%Y")
    n_new = len(new_jobs)
    n_open = len(open_jobs)
    subject = f"Internships & spring weeks — {n_new} new, {n_open} open ({today})"
    new_ids = {job.uid for job in new_jobs}
    romania, remote_eu, spring = split_for_email(open_jobs)

    sections = [
        (
            "Romania internships",
            romania,
            "No matching Romania internships right now.",
        ),
        (
            "Remote internships (EU / EMEA)",
            remote_eu,
            "No remote-EU internships open right now.",
        ),
        (
            "Spring weeks (UK / EU — not internships, not US/Canada)",
            spring,
            "No spring weeks open right now. Typical windows are January–March.",
        ),
    ]

    plain_lines = [
        f"Romania internships + remote-EU internships + spring weeks outside the US/Canada — {today}",
        f"New: {n_new}    Still open: {n_open}",
        "",
        "Each card lists the company name, the role, the city, and the apply URL.",
        "",
    ]
    if not new_jobs:
        plain_lines.append("Nothing new since the last scan. Open roles are listed below.")
        plain_lines.append("")
    for title, jobs, empty in sections:
        plain_lines.extend(_plain_section(title, jobs, new_ids, empty))
    plain = "\n".join(plain_lines)

    cards = [_section_html(title, jobs, new_ids, empty) for title, jobs, empty in sections]

    html_body = f"""
    <html>
      <body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">
        <div style="max-width:640px;margin:0 auto;padding:28px 16px">
          <h1 style="font-size:22px;margin:0 0 8px;color:#0f172a">Internships &amp; spring weeks</h1>
          <p style="margin:0 0 20px;color:#475569">
            SWE / data / quant · Romania internships first · remote-EU internships · spring weeks
            outside the US/Canada · {today}<br>
            <strong>{n_new}</strong> new postings · <strong>{n_open}</strong> still open
          </p>
          {''.join(cards)}
          <p style="margin:28px 0 0;color:#94a3b8;font-size:12px">
            internscout digest. Internships are Romania or remote-EU. Abroad in-office roles only
            keep spring / insight weeks, and we drop US and Canada everywhere.
          </p>
        </div>
      </body>
    </html>
    """
    return subject, plain, html_body


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
