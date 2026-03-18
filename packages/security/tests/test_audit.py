"""Tests for audit logging."""

from __future__ import annotations

from autogenesis_security.audit import AuditLogger


class TestAuditLogger:
    def test_log_entry_creation(self, tmp_path):
        logger = AuditLogger(audit_dir=tmp_path)
        entry = logger.log("tool.call", {"tool": "bash", "command": "ls"})

        assert entry["event_type"] == "tool.call"
        assert "hash" in entry
        assert "timestamp" in entry

    def test_hash_chain_validation(self, tmp_path):
        logger = AuditLogger(audit_dir=tmp_path)
        logger.log("event1")
        logger.log("event2")
        logger.log("event3")

        assert logger.verify_chain() is True

    def test_query_by_event_type(self, tmp_path):
        logger = AuditLogger(audit_dir=tmp_path)
        logger.log("tool.call", {"tool": "bash"})
        logger.log("model.call", {"model": "gpt-4o"})
        logger.log("tool.call", {"tool": "file_read"})

        results = logger.query(event_type="tool.call")
        assert len(results) == 2
        assert all(r["event_type"] == "tool.call" for r in results)

    def test_query_returns_all(self, tmp_path):
        logger = AuditLogger(audit_dir=tmp_path)
        for i in range(5):
            logger.log(f"event_{i}")

        results = logger.query()
        assert len(results) == 5

    def test_daily_rotation(self, tmp_path):
        logger = AuditLogger(audit_dir=tmp_path)
        logger.log("test")

        # File should exist with today's date
        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 1
