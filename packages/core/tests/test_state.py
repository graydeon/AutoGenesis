"""Tests for session state persistence."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from autogenesis_core.models import AgentState, Message
from autogenesis_core.state import StatePersistence


class TestStatePersistence:
    def test_save_and_load(self, tmp_path):
        sp = StatePersistence(base_dir=tmp_path)
        state = AgentState()
        state.messages.append(Message(role="user", content="hello"))

        sp.save(state)
        loaded = sp.load(state.session_id)

        assert loaded is not None
        assert loaded.session_id == state.session_id
        assert len(loaded.messages) == 1
        assert loaded.messages[0].content == "hello"

    def test_load_nonexistent_returns_none(self, tmp_path):
        sp = StatePersistence(base_dir=tmp_path)
        result = sp.load("nonexistent-session-id")
        assert result is None

    def test_atomic_write(self, tmp_path):
        sp = StatePersistence(base_dir=tmp_path)
        state = AgentState()
        sp.save(state)

        # File should exist at expected path
        session_file = tmp_path / f"{state.session_id}.json"
        assert session_file.exists()

        # Should be valid JSON
        data = json.loads(session_file.read_text())
        assert data["session_id"] == state.session_id

    def test_list_sessions(self, tmp_path):
        sp = StatePersistence(base_dir=tmp_path)

        states = [AgentState() for _ in range(3)]
        for s in states:
            sp.save(s)

        sessions = sp.list_sessions()
        assert len(sessions) == 3
        session_ids = {s["session_id"] for s in sessions}
        assert session_ids == {s.session_id for s in states}

    def test_cleanup_old_sessions(self, tmp_path):
        sp = StatePersistence(base_dir=tmp_path)

        # Create an old session by writing directly with old timestamp
        old_state = AgentState()
        old_state.created_at = datetime.now(UTC) - timedelta(days=60)
        old_state.updated_at = old_state.created_at
        sp.save(old_state)

        # Create a recent session
        new_state = AgentState()
        sp.save(new_state)

        removed = sp.cleanup(retention_days=30)
        assert removed == 1

        # Old session gone, new session remains
        assert sp.load(old_state.session_id) is None
        assert sp.load(new_state.session_id) is not None

    def test_save_overwrites_existing(self, tmp_path):
        sp = StatePersistence(base_dir=tmp_path)
        state = AgentState()
        sp.save(state)

        state.messages.append(Message(role="user", content="updated"))
        sp.save(state)

        loaded = sp.load(state.session_id)
        assert loaded is not None
        assert len(loaded.messages) == 1
        assert loaded.messages[0].content == "updated"
