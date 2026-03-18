"""Tests for token budget enforcement."""

from __future__ import annotations

from autogenesis_core.events import EventType, get_event_bus
from autogenesis_tokens.budget import TokenBudget


class TestTokenBudget:
    def test_session_budget_enforcement(self, tmp_path):
        budget = TokenBudget(
            max_tokens_per_session=100,
            max_cost_per_session=1.0,
            budget_path=tmp_path / "budgets.json",
        )
        budget.record_usage(tokens=50, cost=0.5)
        assert not budget.is_session_exceeded()

        budget.record_usage(tokens=60, cost=0.6)
        assert budget.is_session_exceeded()

    def test_daily_budget(self, tmp_path):
        budget = TokenBudget(
            max_cost_per_day=1.0,
            budget_path=tmp_path / "budgets.json",
        )
        budget.record_usage(tokens=100, cost=0.5)
        assert not budget.is_daily_exceeded()

        budget.record_usage(tokens=100, cost=0.6)
        assert budget.is_daily_exceeded()

    def test_warning_at_80_percent(self, tmp_path):
        bus = get_event_bus()
        warnings = []
        bus.subscribe(EventType.TOKEN_BUDGET_WARNING, warnings.append)

        budget = TokenBudget(
            max_cost_per_session=1.0,
            budget_path=tmp_path / "budgets.json",
        )
        budget.record_usage(tokens=50, cost=0.85)  # >= 80%

        assert len(warnings) >= 1

    def test_check_budget_returns_message(self, tmp_path):
        budget = TokenBudget(
            max_cost_per_session=0.01,
            budget_path=tmp_path / "budgets.json",
        )
        budget.record_usage(tokens=100, cost=0.02)
        msg = budget.check_budget()
        assert msg is not None
        assert "exceeded" in msg.lower()

    def test_persistent_tracking(self, tmp_path):
        path = tmp_path / "budgets.json"
        budget1 = TokenBudget(budget_path=path)
        budget1.record_usage(tokens=50, cost=0.1)

        budget2 = TokenBudget(budget_path=path)
        assert budget2.daily_cost >= 0.1

    def test_fresh_budget_not_exceeded(self, tmp_path):
        budget = TokenBudget(budget_path=tmp_path / "budgets.json")
        assert budget.check_budget() is None
        assert budget.session_tokens == 0
