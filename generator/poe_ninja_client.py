"""Thin HTTP client for poe.ninja's PoE2 economy endpoints.

Only hits the small number of category-level overview endpoints (never
per-item), so a full daily run makes on the order of ten requests total —
comfortably inside poe.ninja's stated "don't poll faster than a few minutes"
guidance for these endpoints.
"""

from __future__ import annotations

import time

import requests


class PoeNinjaError(RuntimeError):
    """Raised when a poe.ninja request fails after all retries."""


class PoeNinjaClient:
    def __init__(
        self,
        base_url: str,
        user_agent: str,
        timeout_seconds: float = 15.0,
        max_retries: int = 3,
        retry_backoff_seconds: float = 2.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": user_agent})
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds

    def _get(self, path: str, params: dict) -> dict:
        url = f"{self._base_url}{path}"
        last_error: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                response = self._session.get(url, params=params, timeout=self._timeout_seconds)
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt < self._max_retries:
                    time.sleep(self._retry_backoff_seconds * attempt)
        raise PoeNinjaError(f"GET {url} params={params} failed after {self._max_retries} attempts: {last_error}")

    def get_leagues(self) -> list[dict]:
        return self._get("/poe2/api/economy/leagues", {})

    def get_exchange_overview(self, league: str, currency_type: str) -> dict:
        return self._get(
            "/poe2/api/economy/exchange/current/overview",
            {"league": league, "type": currency_type},
        )

    def get_stash_overview(self, league: str, item_type: str) -> dict:
        return self._get(
            "/poe2/api/economy/stash/current/item/overview",
            {"league": league, "type": item_type},
        )
