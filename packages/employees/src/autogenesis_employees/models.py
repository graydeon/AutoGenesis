"""Employee data models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class EmployeeConfig(BaseModel):
    """Employee configuration loaded from YAML."""

    id: str
    title: str
    persona: str
    tools: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    training_directives: list[str] = Field(default_factory=list)
    status: Literal["active", "archived"] = "active"
    hired_at: str = ""


class Memory(BaseModel):
    """A single memory in an employee's brain.db."""

    id: str = Field(default_factory=lambda: uuid4().hex[:16])
    category: Literal["decision", "pattern", "note", "context", "received"]
    content: str
    source: str
    project: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_accessed_at: datetime | None = None
    relevance_score: float = 1.0


class InboxMessage(BaseModel):
    """An async message between employees."""

    id: str = Field(default_factory=lambda: uuid4().hex[:16])
    from_employee: str
    to_employee: str
    subject: str
    body: str
    status: Literal["unread", "read", "archived"] = "unread"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    read_at: datetime | None = None


class Proposal(BaseModel):
    """A union proposal."""

    id: str = Field(default_factory=lambda: uuid4().hex[:16])
    title: str
    rationale: str
    category: Literal["hiring", "tooling", "process", "architecture", "workload"]
    filed_by: str
    status: Literal["open", "accepted", "rejected", "tabled"] = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None
    resolution: str | None = None


class Vote(BaseModel):
    """A vote on a union proposal."""

    id: str = Field(default_factory=lambda: uuid4().hex[:16])
    proposal_id: str
    employee_id: str
    vote: Literal["support", "neutral", "oppose"]
    comment: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ChangelogEntry(BaseModel):
    """A structured changelog entry."""

    employee_id: str
    task: str
    changes: str
    files: list[str] = Field(default_factory=list)
    notes: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StandupEntry(BaseModel):
    """A daily standup update from an employee."""

    employee_id: str
    yesterday: str
    today: str
    blockers: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
