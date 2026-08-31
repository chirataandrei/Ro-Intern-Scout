from __future__ import annotations

from internscout.config import ENV_PATH, SEEN_PATH, load_dotenv
from internscout.delivery.emailer import build_email, is_remote_eu_job, is_romania_job, send_email
from internscout.pipeline import scan
from internscout.store import load_seen, save_seen, seen_keys_for, split_new


def run(*, send: bool, persist: bool) -> int:
    load_dotenv(ENV_PATH)
    jobs = scan()
    seen = load_seen()
    new_jobs, open_jobs = split_new(jobs, seen)
    romania_n = sum(1 for job in open_jobs if is_romania_job(job))
    remote_n = sum(1 for job in open_jobs if is_remote_eu_job(job))
    spring_n = len(open_jobs) - romania_n - remote_n
    print(
        f"\nOpen: {len(open_jobs)}   New: {len(new_jobs)}   "
        f"Romania: {romania_n}   Remote EU: {remote_n}   Spring weeks: {spring_n}"
    )
    for job in new_jobs[:100]:
        print(f"  [NEW] {job.company} — {job.title} ({job.location})")
        print(f"         {job.url}")

    subject, plain, html_body = build_email(new_jobs, open_jobs)
    if send:
        if not new_jobs:
            print("No new postings — email not sent.")
        else:
            send_email(subject, plain, html_body)
            print(f"Email sent: {subject}")
    if persist:
        updated = seen | seen_keys_for(open_jobs)
        save_seen(updated, SEEN_PATH)
        print(f"Saved {SEEN_PATH} ({len(updated)} ids)")
    return 0
