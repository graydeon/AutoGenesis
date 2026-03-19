"""Twitter browse tool — wraps TwitterBrowser for the agent loop."""

from __future__ import annotations

from typing import Any

from autogenesis_tools.base import Tool


class TwitterBrowseTool(Tool):
    """Browse Twitter feed and return structured tweet data."""

    def __init__(self, browser: Any = None) -> None:  # noqa: ANN401
        self._browser = browser

    @property
    def name(self) -> str:
        return "twitter_browse"

    @property
    def description(self) -> str:
        return "Browse Twitter/X feed and return recent tweets as structured data for analysis."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "max_scrolls": {
                    "type": "integer",
                    "description": "Number of times to scroll for more content (default 3)",
                },
            },
        }

    @property
    def token_cost_estimate(self) -> int:
        return 500

    async def execute(self, arguments: dict[str, Any]) -> str:
        if self._browser is None:
            return "Error: TwitterBrowser not configured"

        max_scrolls = int(arguments.get("max_scrolls", 3))
        tweets = await self._browser.browse_feed(max_scrolls=max_scrolls)

        if not tweets:
            return "No tweets found in feed."

        from autogenesis_twitter.parser import format_tweet_for_llm

        return "\n\n".join(format_tweet_for_llm(t) for t in tweets)
