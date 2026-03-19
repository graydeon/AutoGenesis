"""Tests for TwitterBrowser — Pinchtab MCP wrapper."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from autogenesis_twitter.browser import TwitterBrowser


class TestTwitterBrowser:
    async def test_browse_feed_returns_tweets(self):
        mock_mcp = MagicMock()
        mock_mcp.navigate_to = AsyncMock(return_value={"tabId": "tab1"})
        feed_text = (
            "@airesearcher · 2h\n"
            "New paper on transformer efficiency is really promising\n"
            "3 replies · 5 retweets · 42 likes\n"
        )
        mock_mcp.get_page_text = AsyncMock(return_value={"text": feed_text})
        mock_mcp.evaluate_js = AsyncMock(return_value={"result": "scrolled"})
        mock_mcp.close_tab = AsyncMock()

        browser = TwitterBrowser(mcp_client=mock_mcp)
        tweets = await browser.browse_feed()

        assert len(tweets) >= 1
        assert tweets[0].author == "@airesearcher"

    async def test_browse_feed_handles_empty_page(self):
        mock_mcp = MagicMock()
        mock_mcp.navigate_to = AsyncMock(return_value={"tabId": "tab1"})
        mock_mcp.get_page_text = AsyncMock(return_value={"text": "Loading..."})
        mock_mcp.evaluate_js = AsyncMock(return_value={"result": "scrolled"})
        mock_mcp.close_tab = AsyncMock()

        browser = TwitterBrowser(mcp_client=mock_mcp)
        tweets = await browser.browse_feed()
        assert tweets == []

    async def test_browse_feed_handles_mcp_error(self):
        mock_mcp = MagicMock()
        mock_mcp.navigate_to = AsyncMock(side_effect=Exception("Pinchtab not running"))

        browser = TwitterBrowser(mcp_client=mock_mcp)
        tweets = await browser.browse_feed()
        assert tweets == []
