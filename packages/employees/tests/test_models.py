"""Tests for employee data models."""

from __future__ import annotations

import pytest
from autogenesis_employees.models import (
    ChangelogEntry,
    EmployeeConfig,
    InboxMessage,
    Memory,
    Proposal,
    StandupEntry,
    Vote,
)


class TestEmployeeConfig:
    def test_defaults(self):
        cfg = EmployeeConfig(id="test", title="Test", persona="You are a test agent.")
        assert cfg.status == "active"
        assert cfg.tools == []
        assert cfg.training_directives == []
        assert cfg.env == {}

    def test_serialization_roundtrip(self):
        cfg = EmployeeConfig(
            id="backend-engineer",
            title="Backend Engineer",
            persona="You are a backend engineer.",
            tools=["bash", "file_read"],
        )
        data = cfg.model_dump()
        restored = EmployeeConfig.model_validate(data)
        assert restored.id == "backend-engineer"
        assert "bash" in restored.tools

    def test_valid_status(self):
        EmployeeConfig(id="x", title="X", persona="p", status="active")
        EmployeeConfig(id="x", title="X", persona="p", status="archived")
        with pytest.raises(Exception):
            EmployeeConfig(id="x", title="X", persona="p", status="invalid")


class TestMemory:
    def test_defaults(self):
        m = Memory(category="note", content="test", source="self", project="proj")
        assert m.relevance_score == 1.0
        assert m.id != ""

    def test_valid_categories(self):
        for cat in ["decision", "pattern", "note", "context", "received"]:
            Memory(category=cat, content="x", source="s", project="p")


class TestInboxMessage:
    def test_defaults(self):
        m = InboxMessage(
            from_employee="cto", to_employee="backend-engineer", subject="hi", body="hello"
        )
        assert m.status == "unread"
        assert m.id != ""


class TestProposal:
    def test_defaults(self):
        p = Proposal(title="Hire", rationale="need", category="hiring", filed_by="cto")
        assert p.status == "open"


class TestVote:
    def test_valid_votes(self):
        Vote(proposal_id="p1", employee_id="cto", vote="support")
        Vote(proposal_id="p1", employee_id="cto", vote="neutral")
        Vote(proposal_id="p1", employee_id="cto", vote="oppose")
        with pytest.raises(Exception):
            Vote(proposal_id="p1", employee_id="cto", vote="maybe")


class TestChangelogEntry:
    def test_basic(self):
        e = ChangelogEntry(
            employee_id="backend-engineer",
            task="Build API",
            changes="Added routes",
            files=["api.py"],
        )
        assert e.employee_id == "backend-engineer"


class TestStandupEntry:
    def test_basic(self):
        e = StandupEntry(
            employee_id="qa-engineer", yesterday="Wrote tests", today="Review PR", blockers="None"
        )
        assert e.blockers == "None"
