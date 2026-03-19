"""Synchronous pub/sub event system."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from enum import StrEnum
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import Callable

logger = structlog.get_logger()


class EventType(StrEnum):
    """42 event types using domain.subject.action naming."""

    LOOP_EXECUTION_START = "loop.execution.start"
    LOOP_EXECUTION_ITERATION = "loop.execution.iteration"
    LOOP_EXECUTION_END = "loop.execution.end"
    TOOL_CALL_START = "tool.call.start"
    TOOL_CALL_END = "tool.call.end"
    MODEL_CALL_START = "model.call.start"
    MODEL_CALL_END = "model.call.end"
    TOKEN_BUDGET_WARNING = "token.budget.warning"  # noqa: S105
    TOKEN_BUDGET_EXCEEDED = "token.budget.exceeded"  # noqa: S105
    PROMPT_VERSION_CHANGE = "prompt.version.change"
    SECURITY_GUARDRAIL_ALERT = "security.guardrail.alert"
    CONTEXT_WINDOW_TRUNCATION = "context.window.truncation"
    AUTH_TOKEN_REFRESH = "auth.token.refresh"  # noqa: S105
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILED = "auth.login.failed"
    TWITTER_SESSION_START = "twitter.session.start"
    TWITTER_SESSION_END = "twitter.session.end"
    TWITTER_BROWSE_CYCLE = "twitter.browse.cycle"
    TWITTER_DRAFT_CREATED = "twitter.draft.created"
    TWITTER_DRAFT_POSTED = "twitter.draft.posted"
    TWITTER_GUARDRAIL_VIOLATION = "twitter.guardrail.violation"
    TWITTER_INJECTION_BLOCKED = "twitter.injection.blocked"
    TWITTER_AUTH_REQUIRED = "twitter.auth.required"
    EMPLOYEE_SESSION_START = "employee.session.start"
    EMPLOYEE_SESSION_END = "employee.session.end"
    EMPLOYEE_SESSION_FAILED = "employee.session.failed"
    EMPLOYEE_SESSION_TIMEOUT = "employee.session.timeout"
    EMPLOYEE_MESSAGE_SENT = "employee.message.sent"
    EMPLOYEE_MESSAGE_DELIVERED = "employee.message.delivered"
    EMPLOYEE_STANDUP_POSTED = "employee.standup.posted"
    EMPLOYEE_MEETING_START = "employee.meeting.start"
    EMPLOYEE_MEETING_END = "employee.meeting.end"
    EMPLOYEE_HIRED = "employee.hired"
    EMPLOYEE_FIRED = "employee.fired"
    EMPLOYEE_TRAINED = "employee.trained"
    EMPLOYEE_UNION_PROPOSAL = "employee.union.proposal"
    CEO_GOAL_START = "ceo.goal.start"
    CEO_SUBTASK_ASSIGN = "ceo.subtask.assign"
    CEO_SUBTASK_COMPLETE = "ceo.subtask.complete"
    CEO_SUBTASK_FAIL = "ceo.subtask.fail"
    CEO_ESCALATION = "ceo.escalation"
    CEO_GOAL_COMPLETE = "ceo.goal.complete"


class Event(BaseModel):
    """A typed event with timestamp and arbitrary data payload."""

    event_type: EventType
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EventBus:
    """Synchronous publish/subscribe event bus.

    Exception-safe: handler errors are logged but do not prevent
    other handlers from executing.
    """

    def __init__(self) -> None:
        self._handlers: defaultdict[EventType, list[Callable[[Event], None]]] = defaultdict(list)

    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Register a handler for an event type."""
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Remove a handler for an event type."""
        handlers = self._handlers[event_type]
        self._handlers[event_type] = [h for h in handlers if h is not handler]

    def emit(self, event: Event) -> None:
        """Emit an event to all registered handlers."""
        for handler in self._handlers.get(event.event_type, []):
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "event_handler_error",
                    event_type=event.event_type.value,
                    handler=getattr(handler, "__name__", repr(handler)),
                )


@lru_cache(maxsize=1)
def get_event_bus() -> EventBus:
    """Return global singleton EventBus instance."""
    return EventBus()
