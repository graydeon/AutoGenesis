"""Tests for Twitter session scheduler."""

from __future__ import annotations

from datetime import UTC, datetime

from autogenesis_twitter.scheduler import is_within_active_hours


class TestActiveHours:
    def test_within_hours(self):
        now = datetime(2026, 3, 18, 12, 0, tzinfo=UTC)
        assert is_within_active_hours(now, "09:00", "17:00", "UTC") is True

    def test_before_hours(self):
        now = datetime(2026, 3, 18, 7, 0, tzinfo=UTC)
        assert is_within_active_hours(now, "09:00", "17:00", "UTC") is False

    def test_after_hours(self):
        now = datetime(2026, 3, 18, 18, 0, tzinfo=UTC)
        assert is_within_active_hours(now, "09:00", "17:00", "UTC") is False

    def test_at_start(self):
        now = datetime(2026, 3, 18, 9, 0, tzinfo=UTC)
        assert is_within_active_hours(now, "09:00", "17:00", "UTC") is True

    def test_at_end(self):
        now = datetime(2026, 3, 18, 17, 0, tzinfo=UTC)
        assert is_within_active_hours(now, "09:00", "17:00", "UTC") is False
