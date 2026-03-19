"""Twitter post tool — queues drafts for human approval."""

from __future__ import annotations

from typing import Any

from autogenesis_tools.base import Tool


class TwitterPostTool(Tool):
    """Queue a tweet draft for human approval. Never posts directly."""

    def __init__(self, queue_manager: Any = None) -> None:  # noqa: ANN401
        self._queue = queue_manager

    @property
    def name(self) -> str:
        return "twitter_post"

    @property
    def description(self) -> str:
        return (
            "Queue a tweet or reply for human approval. The tweet will NOT be posted "
            "immediately — it goes into a review queue. Use type='original' for new tweets "
            "or type='reply' with reply_to_id for replies."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Tweet text (max 280 chars)"},
                "type": {
                    "type": "string",
                    "enum": ["original", "reply"],
                    "description": "Tweet type",
                },
                "reply_to_id": {
                    "type": "string",
                    "description": "Tweet ID to reply to (required if type=reply)",
                },
            },
            "required": ["text", "type"],
        }

    @property
    def token_cost_estimate(self) -> int:
        return 150

    async def execute(self, arguments: dict[str, Any]) -> str:
        if self._queue is None:
            return "Error: QueueManager not configured"

        from autogenesis_twitter.guardrails import ConstitutionalCheck
        from autogenesis_twitter.models import QueueItem

        text = arguments["text"]
        tweet_type = arguments["type"]

        # Constitutional self-check before queuing
        check = ConstitutionalCheck()
        result = check.check(text)
        if not result.passed:
            return f"Draft rejected by constitutional check: {result.reason}"

        item = QueueItem(type=tweet_type, draft_text=text)
        await self._queue.add(item)

        return f"Draft queued for approval (id: {item.id}). It will be posted after human review."
