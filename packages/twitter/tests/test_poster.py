"""Tests for TwitterPoster — gateway HTTP client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
from autogenesis_twitter.poster import TwitterPoster


class TestTwitterPoster:
    async def test_post_tweet_success(self):
        poster = TwitterPoster(gateway_url="http://localhost:1456", gateway_token="test_token")  # noqa: S106
        mock_response = httpx.Response(200, json={"id": "12345", "status": "posted"})
        with patch.object(poster._http, "post", new_callable=AsyncMock, return_value=mock_response):
            result = await poster.post_tweet("hello world")
            assert result.success is True
            assert result.tweet_id == "12345"
        await poster.close()

    async def test_post_reply_success(self):
        poster = TwitterPoster(gateway_url="http://localhost:1456", gateway_token="test_token")  # noqa: S106
        mock_response = httpx.Response(200, json={"id": "12346", "status": "posted"})
        with patch.object(poster._http, "post", new_callable=AsyncMock, return_value=mock_response):
            result = await poster.post_tweet("great take", reply_to_id="99999")
            assert result.success is True
        await poster.close()

    async def test_rate_limit_error(self):
        poster = TwitterPoster(gateway_url="http://localhost:1456", gateway_token="test_token")  # noqa: S106
        mock_response = httpx.Response(429, json={"error": "rate limited", "code": 429})
        with patch.object(poster._http, "post", new_callable=AsyncMock, return_value=mock_response):
            result = await poster.post_tweet("hello", max_retries=1)
            assert result.success is False
            assert "rate" in result.error.lower()
        await poster.close()

    async def test_auth_error(self):
        poster = TwitterPoster(gateway_url="http://localhost:1456", gateway_token="test_token")  # noqa: S106
        mock_response = httpx.Response(401, json={"error": "unauthorized", "code": 401})
        with patch.object(poster._http, "post", new_callable=AsyncMock, return_value=mock_response):
            result = await poster.post_tweet("hello")
            assert result.success is False
        await poster.close()

    async def test_gateway_status(self):
        poster = TwitterPoster(gateway_url="http://localhost:1456", gateway_token="test_token")  # noqa: S106
        mock_response = httpx.Response(
            200, json={"authenticated": True, "rate_limit_remaining": 142}
        )
        with patch.object(poster._http, "get", new_callable=AsyncMock, return_value=mock_response):
            status = await poster.get_status()
            assert status["authenticated"] is True
        await poster.close()
