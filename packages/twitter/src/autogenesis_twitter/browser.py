"""TwitterBrowser — Pinchtab MCP wrapper for browsing Twitter.

Uses Pinchtab's navigate_to, get_page_text, evaluate_js to browse
Twitter like a human. All content passes through the parser for
structured extraction before reaching the agent.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Protocol

import structlog

from autogenesis_twitter.parser import extract_tweets_from_text

if TYPE_CHECKING:
    from autogenesis_twitter.models import TweetData

logger = structlog.get_logger()

_TWITTER_HOME = "https://twitter.com/home"
_SCROLL_JS = "window.scrollBy(0, window.innerHeight * 2); 'scrolled'"


class McpClient(Protocol):
    """Minimal protocol for Pinchtab MCP client."""

    async def navigate_to(self, *, url: str) -> dict[str, object]:
        """Navigate to a URL and return tab info."""
        ...

    async def get_page_text(self, *, tabId: str) -> dict[str, object]:  # noqa: N803
        """Return page text for a tab."""
        ...

    async def evaluate_js(self, *, tabId: str, script: str) -> dict[str, object]:  # noqa: N803
        """Evaluate JS in a tab."""
        ...

    async def close_tab(self, *, tabId: str) -> None:  # noqa: N803
        """Close a tab."""
        ...


class TwitterBrowser:
    """Browse Twitter via Pinchtab MCP server."""

    def __init__(self, mcp_client: McpClient) -> None:
        self._mcp = mcp_client

    async def browse_feed(self, max_scrolls: int = 3) -> list[TweetData]:
        """Navigate to Twitter home feed, scroll, extract tweets."""
        try:
            tab = await self._mcp.navigate_to(url=_TWITTER_HOME)
            tab_id = tab.get("tabId") if isinstance(tab, dict) else str(tab)
        except Exception:  # noqa: BLE001
            logger.warning("twitter_browse_failed", reason="navigate failed")
            return []

        all_tweets: list[TweetData] = []

        try:
            for scroll in range(max_scrolls):
                try:
                    page = await self._mcp.get_page_text(tabId=str(tab_id))
                    text = page.get("text", "") if isinstance(page, dict) else str(page)
                    tweets = extract_tweets_from_text(str(text))
                    for tweet in tweets:
                        if not any(
                            t.id == tweet.id and t.author == tweet.author for t in all_tweets
                        ):
                            all_tweets.append(tweet)

                    await self._mcp.evaluate_js(tabId=str(tab_id), script=_SCROLL_JS)
                except Exception:  # noqa: BLE001
                    logger.warning("twitter_scroll_failed", scroll=scroll)
                    break
        finally:
            with contextlib.suppress(Exception):
                await self._mcp.close_tab(tabId=str(tab_id))

        logger.info("twitter_browse_complete", tweets_found=len(all_tweets))
        return all_tweets
