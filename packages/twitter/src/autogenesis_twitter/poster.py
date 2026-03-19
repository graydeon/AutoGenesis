"""TwitterPoster — gateway HTTP client for posting tweets.

Never accesses Twitter API directly. Sends requests to the host-side
gateway which signs them with real API keys.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()


@dataclass
class PostResult:
    """Result from a tweet post attempt."""

    success: bool
    tweet_id: str = ""
    error: str = ""


class TwitterPoster:
    """Async client for the Twitter posting gateway."""

    def __init__(self, gateway_url: str, gateway_token: str) -> None:
        self._gateway_url = gateway_url.rstrip("/")
        self._token = gateway_token
        self._http = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close HTTP client."""
        await self._http.aclose()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def post_tweet(
        self,
        text: str,
        reply_to_id: str | None = None,
        max_retries: int = 3,
    ) -> PostResult:
        """Post a tweet via the gateway with retry/backoff."""
        body: dict[str, Any] = {"text": text}
        if reply_to_id:
            body["reply_to_id"] = reply_to_id

        for attempt in range(max_retries):
            try:
                response = await self._http.post(
                    f"{self._gateway_url}/twitter/tweet",
                    json=body,
                    headers=self._headers(),
                )
            except httpx.HTTPError as exc:
                logger.warning("gateway_request_failed", error=str(exc), attempt=attempt)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                return PostResult(success=False, error=f"Network error: {exc}")

            data = response.json()

            if response.status_code == 200:  # noqa: PLR2004
                return PostResult(success=True, tweet_id=data.get("id", ""))

            # Rate limit — retry with backoff
            if response.status_code == 429 and attempt < max_retries - 1:  # noqa: PLR2004
                wait = 2 ** (attempt + 1)
                logger.warning("rate_limited", wait=wait, attempt=attempt)
                await asyncio.sleep(wait)
                continue

            error_msg = data.get("error", f"HTTP {response.status_code}")
            logger.warning("tweet_post_failed", status=response.status_code, error=error_msg)
            return PostResult(success=False, error=error_msg)

        return PostResult(success=False, error="Max retries exceeded")

    async def get_status(self) -> dict[str, Any]:
        """Check gateway/Twitter API status."""
        try:
            response = await self._http.get(
                f"{self._gateway_url}/twitter/status",
                headers=self._headers(),
            )
            return response.json()
        except httpx.HTTPError as exc:
            return {"authenticated": False, "error": str(exc)}
