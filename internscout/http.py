from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

USER_AGENT = (
    "Mozilla/5.0 (compatible; internscout/0.1; +https://github.com/chirataandrei/ro-intern-scout)"
)
DEFAULT_TIMEOUT = 25
REQUEST_GAP_SECONDS = 0.35


class HttpClient:
    def __init__(self, timeout: float = DEFAULT_TIMEOUT, gap: float = REQUEST_GAP_SECONDS) -> None:
        self.timeout = timeout
        self.gap = gap
        self._last = 0.0

    def _throttle(self) -> None:
        wait = self.gap - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()

    def request(
        self,
        url: str,
        *,
        method: str = "GET",
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        retries: int = 2,
    ) -> tuple[int, str]:
        hdrs = {"User-Agent": USER_AGENT, "Accept": "application/json, text/html;q=0.9, */*;q=0.8"}
        if headers:
            hdrs.update(headers)
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        last_error = ""
        for attempt in range(retries + 1):
            self._throttle()
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read().decode("utf-8", "replace")
                    return int(resp.status), body
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", "replace") if exc.fp else ""
                if exc.code in {429, 500, 502, 503, 504} and attempt < retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                return int(exc.code), body
            except Exception as exc:  # noqa: BLE001 — network noise is expected
                last_error = str(exc)
                if attempt < retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                return 0, last_error
        return 0, last_error

    def get(self, url: str, **kwargs: Any) -> tuple[int, str]:
        return self.request(url, **kwargs)

    def get_json(self, url: str, **kwargs: Any) -> tuple[int, Any]:
        status, body = self.get(url, **kwargs)
        if status != 200:
            return status, None
        try:
            return status, json.loads(body)
        except json.JSONDecodeError:
            return status, None

    def post_json(self, url: str, payload: dict[str, Any], extra_headers: dict[str, str] | None = None) -> tuple[int, Any]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if extra_headers:
            headers.update(extra_headers)
        status, body = self.request(
            url,
            method="POST",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
        )
        if status != 200:
            return status, None
        try:
            return status, json.loads(body)
        except json.JSONDecodeError:
            return status, None
