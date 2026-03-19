"""Twitter data models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

_MAX_TWEET_TEXT_LEN = 500


class TweetMetrics(BaseModel):
    """Engagement metrics for a tweet."""

    likes: int = 0
    retweets: int = 0
    replies: int = 0


class TweetData(BaseModel):
    """Structured tweet data extracted from page content."""

    id: str
    author: str
    text: str
    metrics: TweetMetrics = Field(default_factory=TweetMetrics)
    timestamp: str
    is_reply_to: str | None = None

    @field_validator("text")
    @classmethod
    def truncate_text(cls, v: str) -> str:
        return v[:_MAX_TWEET_TEXT_LEN] if len(v) > _MAX_TWEET_TEXT_LEN else v


class QueueItem(BaseModel):
    """A draft tweet/reply awaiting approval."""

    id: str = Field(default_factory=lambda: uuid4().hex[:16])
    type: Literal["reply", "original"]
    status: Literal["pending", "approved", "rejected", "posted", "failed"] = "pending"
    draft_text: str
    in_reply_to: TweetData | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reviewed_at: datetime | None = None
    posted_at: datetime | None = None
    rejection_reason: str | None = None
    failure_reason: str | None = None


class Opinion(BaseModel):
    """A formed opinion on a topic."""

    topic: str
    stance: str
    formed_from: str = ""
    date: str = ""


class EngagementStats(BaseModel):
    """Rolling engagement statistics."""

    avg_likes_on_replies: float = 0.0
    style_notes: str = ""


class WorldviewState(BaseModel):
    """The agent's accumulated worldview."""

    topics_of_interest: list[str] = Field(default_factory=list)
    people_i_engage_with: list[str] = Field(default_factory=list)
    opinions_formed: list[Opinion] = Field(default_factory=list)
    engagement_stats: EngagementStats = Field(default_factory=EngagementStats)


class SessionState(BaseModel):
    """Current Twitter session state."""

    active: bool = False
    permission_granted: bool = False
    last_cycle_at: datetime | None = None
    cycles_today: int = 0
    drafts_today: int = 0
