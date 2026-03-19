"""Twitter session scheduler — permission gate and cycle orchestration.

Manages active hours, permission flow, and the browse-reason-draft cycle.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

import structlog
from autogenesis_core.events import Event, EventType, get_event_bus

from autogenesis_twitter.models import SessionState

logger = structlog.get_logger()


def is_within_active_hours(
    now: datetime,
    start: str,
    end: str,
    tz_name: str,
) -> bool:
    """Check if current time is within active hours."""
    tz = ZoneInfo(tz_name)
    local_now = now.astimezone(tz)
    start_hour, start_min = map(int, start.split(":"))
    end_hour, end_min = map(int, end.split(":"))

    start_time = local_now.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
    end_time = local_now.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)

    return start_time <= local_now < end_time


class TwitterScheduler:
    """Manages Twitter session lifecycle."""

    def __init__(
        self,
        active_hours_start: str = "09:00",
        active_hours_end: str = "17:00",
        timezone_name: str = "America/New_York",
        interval_minutes: int = 30,
    ) -> None:
        self._start = active_hours_start
        self._end = active_hours_end
        self._tz = timezone_name
        self._interval = interval_minutes
        self._state = SessionState()

    @property
    def state(self) -> SessionState:
        return self._state

    def is_active_window(self) -> bool:
        """Check if we're in the active hours window."""
        return is_within_active_hours(
            datetime.now(UTC),
            self._start,
            self._end,
            self._tz,
        )

    def grant_permission(self) -> None:
        """User grants permission to start browsing."""
        self._state.permission_granted = True
        self._state.active = True
        bus = get_event_bus()
        bus.emit(Event(event_type=EventType.TWITTER_SESSION_START, data={}))
        logger.info("twitter_session_started")

    def revoke_permission(self) -> None:
        """User revokes permission."""
        self._state.permission_granted = False
        self._state.active = False
        bus = get_event_bus()
        bus.emit(Event(event_type=EventType.TWITTER_SESSION_END, data={}))
        logger.info("twitter_session_stopped")

    def should_run_cycle(self) -> bool:
        """Check if a cycle should run now."""
        if not self._state.active or not self._state.permission_granted:
            return False
        if not self.is_active_window():
            self.revoke_permission()
            return False
        return True

    async def run_cycle(  # noqa: PLR0913
        self,
        browser: Any,  # noqa: ANN401
        queue: Any,  # noqa: ANN401
        poster: Any,  # noqa: ANN401
        worldview_mgr: Any,  # noqa: ANN401, ARG002
        pre_filter: Any,  # noqa: ANN401
        constitutional: Any,  # noqa: ANN401, ARG002
        max_drafts: int = 10,  # noqa: ARG002
    ) -> dict[str, int]:
        """Run a single browse -> filter -> post-approved cycle.

        Returns stats: {"tweets_seen": N, "filtered": N, "drafted": N, "posted": N}

        Note: The full reasoning step (which tweets to engage with, draft responses)
        happens inside the Codex agent loop when the agent uses TwitterBrowseTool
        and TwitterPostTool. The scheduler orchestrates the surrounding infrastructure:
        browsing, filtering, posting approved items, and updating state.
        """
        stats = {"tweets_seen": 0, "filtered": 0, "drafted": 0, "posted": 0}
        bus = get_event_bus()
        bus.emit(Event(event_type=EventType.TWITTER_BROWSE_CYCLE, data={}))

        # Step 1-2: Browse feed
        tweets = await browser.browse_feed()
        stats["tweets_seen"] = len(tweets)

        # Step 3: Filter
        engaged = [t for t in tweets if pre_filter.should_engage(t)]
        stats["filtered"] = len(tweets) - len(engaged)

        # Step 9: Post approved items from queue
        approved = await queue.list_approved()
        for item in approved:
            result = await poster.post_tweet(
                item.draft_text,
                reply_to_id=item.in_reply_to.id if item.in_reply_to else None,
            )
            if result.success:
                await queue.mark_posted(item.id)
                stats["posted"] += 1
                bus.emit(Event(event_type=EventType.TWITTER_DRAFT_POSTED, data={"id": item.id}))
            else:
                await queue.mark_failed(item.id, reason=result.error)

        # Update session state
        self._state.cycles_today += 1
        self._state.last_cycle_at = datetime.now(UTC)

        logger.info("twitter_cycle_complete", **stats)
        return stats
