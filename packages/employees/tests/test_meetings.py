"""Tests for MeetingManager — standups and on-demand meetings."""

from __future__ import annotations

from datetime import UTC, datetime

from autogenesis_employees.meetings import MeetingManager, is_standup_due
from autogenesis_employees.models import StandupEntry


class TestIsStandupDue:
    def test_due_when_no_previous(self):
        assert is_standup_due(last_run=None, standup_time="09:00", tz_name="UTC") is True

    def test_not_due_if_already_ran_today(self):
        today = datetime.now(UTC).date().isoformat()
        assert is_standup_due(last_run=today, standup_time="09:00", tz_name="UTC") is False

    def test_due_if_ran_yesterday(self):
        assert is_standup_due(last_run="2020-01-01", standup_time="09:00", tz_name="UTC") is True


class TestMeetingManager:
    def test_write_standup(self, tmp_path):
        mgr = MeetingManager(meetings_dir=tmp_path)
        entries = [
            StandupEntry(
                employee_id="be", yesterday="Built API", today="Write tests", blockers="None"
            ),
            StandupEntry(
                employee_id="qa",
                yesterday="Reviewed PR",
                today="Test auth",
                blockers="Waiting on BE",
            ),
        ]
        path = mgr.write_standup(entries)
        assert path.exists()
        content = path.read_text()
        assert "be" in content
        assert "qa" in content
        assert "Built API" in content

    def test_write_meeting_transcript(self, tmp_path):
        mgr = MeetingManager(meetings_dir=tmp_path)
        rounds = [
            {"employee": "cto", "response": "I think we should refactor"},
            {"employee": "be", "response": "Agree, the auth module is getting complex"},
        ]
        path = mgr.write_meeting("Refactor auth?", rounds)
        assert path.exists()
        content = path.read_text()
        assert "Refactor auth?" in content
        assert "cto" in content
