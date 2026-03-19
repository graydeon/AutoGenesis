"""Tests for ChangelogManager — append-only markdown writer."""

from __future__ import annotations

from autogenesis_employees.changelog import ChangelogManager
from autogenesis_employees.models import ChangelogEntry


class TestChangelogManager:
    def test_write_entry(self, tmp_path):
        path = tmp_path / "CHANGELOG.md"
        mgr = ChangelogManager(path)
        entry = ChangelogEntry(
            employee_id="backend-engineer",
            task="Build auth API",
            changes="Added login endpoint",
            files=["auth.py"],
            notes="Uses JWT",
        )
        mgr.write(entry)
        content = path.read_text()
        assert "backend-engineer" in content
        assert "Build auth API" in content
        assert "auth.py" in content

    def test_append_only(self, tmp_path):
        path = tmp_path / "CHANGELOG.md"
        mgr = ChangelogManager(path)
        mgr.write(ChangelogEntry(employee_id="a", task="Task 1", changes="c1"))
        mgr.write(ChangelogEntry(employee_id="b", task="Task 2", changes="c2"))
        content = path.read_text()
        assert "Task 1" in content
        assert "Task 2" in content

    def test_read_recent(self, tmp_path):
        path = tmp_path / "CHANGELOG.md"
        mgr = ChangelogManager(path)
        for i in range(15):
            mgr.write(ChangelogEntry(employee_id="e", task=f"Task {i}", changes=f"c{i}"))
        recent = mgr.read_recent(limit=10)
        assert len(recent) <= 10

    def test_read_empty(self, tmp_path):
        path = tmp_path / "CHANGELOG.md"
        mgr = ChangelogManager(path)
        assert mgr.read_recent() == []
