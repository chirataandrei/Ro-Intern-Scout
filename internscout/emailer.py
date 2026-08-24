from __future__ import annotations

import html
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from internscout.models import Job

CATEGORY_LABELS = {
    "faang": "FAANG / big tech",
    "quant": "Quant / trading",
    "product": "Product",
    "gaming": "Gaming",
    "rd": "R&D / automotive",
    "telecom": "Telecom",
    "finance": "Finance tech",
    "ssc": "SSC / outsourcing",
    "aggregator": "Hipo / eJobs / BestJobs",
    "other": "Other",
}


def _esc(text: str) -> str:
    return html.escape(text or "", quote=True)


def build_email(new_jobs: list[Job], open_jobs: list[Job]) -> tuple[str, str, str]:
    today = datetime.now(ZoneInfo("Europe/Bucharest")).strftime("%d.%m.%Y")
    n_new = len(new_jobs)
    n_open = len(open_jobs)
    subject = f"Internships & spring weeks — {n_new} new, {n_open} open ({today})"

    plain_lines = [
        f"Romania internships + quant spring weeks / student programmes — {today}",
        f"New: {n_new}    Still open: {n_open}",
        "",
    ]
    if not new_jobs:
        plain_lines.append("Nothing new since the last scan.")
        plain_lines.append("")
    grouped: dict[str, list[Job]] = defaultdict(list)
    for job in new_jobs or open_jobs[:40]:
        grouped[job.category].append(job)
    if new_jobs:
        for cat, jobs in grouped.items():
            plain_lines.append(CATEGORY_LABELS.get(cat, cat))
            for job in jobs:
                plain_lines.append(f"- {job.company}: {job.title} ({job.location})")
                plain_lines.append(f"  {job.url}")
            plain_lines.append("")
    plain = "\n".join(plain_lines)

    cards = []
    source_jobs = new_jobs if new_jobs else []
    grouped_html: dict[str, list[Job]] = defaultdict(list)
    for job in source_jobs:
        grouped_html[job.category].append(job)

    if not source_jobs:
        cards.append(
            "<p style='margin:0 0 16px;color:#334155'>Nothing new since yesterday. "
            f"<strong>{n_open}</strong> internships remain open in the catalog.</p>"
        )
    for cat, jobs in grouped_html.items():
        cards.append(
            f"<h2 style='font-size:15px;margin:24px 0 10px;color:#0f172a'>"
            f"{_esc(CATEGORY_LABELS.get(cat, cat))}</h2>"
        )
        for job in jobs:
            cards.append(
                f"""
                <div style="border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px;margin:0 0 10px">
                  <div style="font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:.04em">{_esc(job.company)}</div>
                  <a href="{_esc(job.url)}" style="color:#1d4ed8;font-size:16px;font-weight:600;text-decoration:none">{_esc(job.title)}</a>
                  <div style="color:#475569;font-size:13px;margin-top:4px">{_esc(job.location)}</div>
                </div>
                """
            )

    html_body = f"""
    <html>
      <body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">
        <div style="max-width:640px;margin:0 auto;padding:28px 16px">
          <h1 style="font-size:22px;margin:0 0 8px;color:#0f172a">Internships &amp; spring weeks</h1>
          <p style="margin:0 0 20px;color:#475569">SWE / data / quant · Romania + quant student programmes · {today}<br>
            <strong>{n_new}</strong> new postings · <strong>{n_open}</strong> still open</p>
          {''.join(cards)}
          <p style="margin:28px 0 0;color:#94a3b8;font-size:12px">
            internscout digest. Regular internships are filtered to Romania;
            spring weeks and quant-firm internships also include UK/EU/US.
          </p>
        </div>
      </body>
    </html>
    """
    return subject, plain, html_body
