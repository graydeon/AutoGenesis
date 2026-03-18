"""Token budget enforcement."""

from __future__ import annotations

import contextlib
import json
from datetime import UTC, datetime
from os import environ
from pathlib import Path
from typing import Any

import structlog
from autogenesis_core.events import Event, EventType, get_event_bus

logger = structlog.get_logger()

_WARNING_THRESHOLD = 0.8  # 80%


def _default_budget_path() -> Path:
    xdg_state = environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))
    return Path(xdg_state) / "autogenesis" / "budgets.json"


class TokenBudget:
    """Session, daily, and monthly budget enforcement with persistence."""

    def __init__(
        self,
        max_tokens_per_session: int = 100_000,
        max_cost_per_session: float = 5.0,
        max_cost_per_day: float = 50.0,
        max_cost_per_month: float = 500.0,
        budget_path: Path | None = None,
    ) -> None:
        self._max_tokens_session = max_tokens_per_session
        self._max_cost_session = max_cost_per_session
        self._max_cost_day = max_cost_per_day
        self._max_cost_month = max_cost_per_month
        self._path = budget_path or _default_budget_path()

        self._session_tokens = 0
        self._session_cost = 0.0
        self._daily_cost = 0.0
        self._monthly_cost = 0.0

        self._load()

    def _load(self) -> None:
        """Load persistent budget data."""
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text())
            today = datetime.now(UTC).strftime("%Y-%m-%d")
            month = datetime.now(UTC).strftime("%Y-%m")
            self._daily_cost = data.get("daily", {}).get(today, 0.0)
            self._monthly_cost = data.get("monthly", {}).get(month, 0.0)
        except (json.JSONDecodeError, KeyError):
            pass

    def _save(self) -> None:
        """Persist budget data."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        month = datetime.now(UTC).strftime("%Y-%m")

        data: dict[str, Any] = {}
        if self._path.exists():
            with contextlib.suppress(json.JSONDecodeError):
                data = json.loads(self._path.read_text())

        data.setdefault("daily", {})[today] = self._daily_cost
        data.setdefault("monthly", {})[month] = self._monthly_cost

        self._path.write_text(json.dumps(data, indent=2))

    def record_usage(self, tokens: int, cost: float) -> None:
        """Record token usage and check budgets."""
        self._session_tokens += tokens
        self._session_cost += cost
        self._daily_cost += cost
        self._monthly_cost += cost

        bus = get_event_bus()

        # Check warning thresholds
        if self._session_cost >= self._max_cost_session * _WARNING_THRESHOLD:
            bus.emit(
                Event(
                    event_type=EventType.TOKEN_BUDGET_WARNING,
                    data={
                        "level": "session",
                        "usage": self._session_cost,
                        "limit": self._max_cost_session,
                    },
                )
            )

        if self._daily_cost >= self._max_cost_day * _WARNING_THRESHOLD:
            bus.emit(
                Event(
                    event_type=EventType.TOKEN_BUDGET_WARNING,
                    data={"level": "daily", "usage": self._daily_cost, "limit": self._max_cost_day},
                )
            )

        self._save()

    @property
    def session_tokens(self) -> int:
        return self._session_tokens

    @property
    def session_cost(self) -> float:
        return self._session_cost

    @property
    def daily_cost(self) -> float:
        return self._daily_cost

    @property
    def monthly_cost(self) -> float:
        return self._monthly_cost

    def is_session_exceeded(self) -> bool:
        return (
            self._session_tokens >= self._max_tokens_session
            or self._session_cost >= self._max_cost_session
        )

    def is_daily_exceeded(self) -> bool:
        return self._daily_cost >= self._max_cost_day

    def is_monthly_exceeded(self) -> bool:
        return self._monthly_cost >= self._max_cost_month

    def check_budget(self) -> str | None:
        """Return error message if any budget exceeded, else None."""
        if self.is_session_exceeded():
            return (
                f"Session budget exceeded: "
                f"${self._session_cost:.4f} >= ${self._max_cost_session}"
            )
        if self.is_daily_exceeded():
            return f"Daily budget exceeded: ${self._daily_cost:.4f} >= ${self._max_cost_day}"
        if self.is_monthly_exceeded():
            return f"Monthly budget exceeded: ${self._monthly_cost:.4f} >= ${self._max_cost_month}"
        return None
