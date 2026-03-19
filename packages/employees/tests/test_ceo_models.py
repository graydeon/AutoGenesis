"""Tests for CEO orchestrator data models."""

from __future__ import annotations

from autogenesis_employees.ceo_models import (
    GoalResult,
    GoalStatus,
    ManagerBundle,
    SubtaskResult,
    TaskResult,
    TaskStatus,
)


class TestManagerBundle:
    def test_dataclass_fields(self):
        """ManagerBundle has brain and inbox fields."""
        bundle = ManagerBundle(brain=None, inbox=None)
        assert hasattr(bundle, "brain")
        assert hasattr(bundle, "inbox")


class TestSubtaskResult:
    def test_creation(self):
        r = SubtaskResult(
            subtask="Build API",
            employee_id="backend-engineer",
            status="completed",
            output="Done",
            attempt=1,
            duration_seconds=42.5,
        )
        assert r.subtask == "Build API"
        assert r.employee_id == "backend-engineer"
        assert r.status == "completed"
        assert r.attempt == 1
        assert r.duration_seconds == 42.5


class TestGoalResult:
    def test_creation(self):
        r = GoalResult(
            goal_id="abc123",
            status="completed",
            subtask_results=[],
            plan_path="/tmp/plan.md",
        )
        assert r.goal_id == "abc123"
        assert r.status == "completed"
        assert r.subtask_results == []

    def test_with_subtasks(self):
        sub = SubtaskResult(
            subtask="test",
            employee_id="qa",
            status="completed",
            output="ok",
            attempt=1,
            duration_seconds=10.0,
        )
        r = GoalResult(
            goal_id="abc",
            status="completed",
            subtask_results=[sub],
            plan_path="/tmp/plan.md",
        )
        assert len(r.subtask_results) == 1


class TestTaskResult:
    def test_defaults(self):
        r = TaskResult(task_id="t1", status="completed")
        assert r.employee_id is None
        assert r.output == ""
        assert r.duration_seconds == 0.0


class TestGoalStatus:
    def test_creation(self):
        s = GoalStatus(
            goal_id="g1",
            description="Build feature",
            status="executing",
            subtasks_completed=2,
            subtasks_total=5,
            plan_path="/tmp/plan.md",
        )
        assert s.subtasks_completed == 2
        assert s.subtasks_total == 5


class TestTaskStatus:
    def test_creation(self):
        s = TaskStatus(
            task_id="t1",
            description="Fix bug",
            status="pending",
            priority=5,
        )
        assert s.priority == 5
