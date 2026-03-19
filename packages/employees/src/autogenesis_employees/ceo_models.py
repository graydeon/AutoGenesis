"""CEO Orchestrator data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from autogenesis_employees.brain import BrainManager
    from autogenesis_employees.inbox import InboxManager


@dataclass
class ManagerBundle:
    """Per-employee lazily-initialized manager pair."""

    brain: BrainManager
    inbox: InboxManager


class SubtaskResult(BaseModel):
    """Result from a single subtask dispatch."""

    subtask: str
    employee_id: str
    status: str  # completed / failed / escalated
    output: str
    attempt: int
    duration_seconds: float


class GoalResult(BaseModel):
    """Result from a full goal execution."""

    goal_id: str
    status: str  # completed / escalated
    subtask_results: list[SubtaskResult]
    plan_path: str


class TaskResult(BaseModel):
    """Result from a standalone task dispatch."""

    task_id: str
    status: str  # completed / failed / escalated
    employee_id: str | None = None
    output: str = ""
    duration_seconds: float = 0.0


class GoalStatus(BaseModel):
    """Status snapshot of a goal."""

    goal_id: str
    description: str
    status: str
    subtasks_completed: int
    subtasks_total: int
    plan_path: str


class TaskStatus(BaseModel):
    """Status snapshot of a queued task."""

    task_id: str
    description: str
    status: str
    priority: int
