from __future__ import annotations

def uid(source: str, token: str, job_id: str) -> str:
    return f"{source}:{token}:{job_id}"
