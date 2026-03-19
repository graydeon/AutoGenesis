"""Tests for CEOStateManager — SQLite CRUD for ceo.db."""

from __future__ import annotations

import pytest
from autogenesis_employees.state import CEOStateManager


class TestCEOStateManager:
    @pytest.fixture
    async def state(self, tmp_path):
        mgr = CEOStateManager(db_path=tmp_path / "ceo.db")
        await mgr.initialize()
        yield mgr
        await mgr.close()

    async def test_create_and_get_task(self, state):
        task_id = await state.create_task("Fix the login bug", priority=5)
        task = await state.get_task(task_id)
        assert task is not None
        assert task["description"] == "Fix the login bug"
        assert task["priority"] == 5
        assert task["status"] == "pending"

    async def test_list_pending_tasks(self, state):
        await state.create_task("Low priority", priority=1)
        await state.create_task("High priority", priority=10)
        tasks = await state.list_pending_tasks()
        assert len(tasks) == 2
        assert tasks[0]["priority"] == 10

    async def test_update_task_status(self, state):
        task_id = await state.create_task("Test task")
        await state.update_task(task_id, status="completed", result="Done")
        task = await state.get_task(task_id)
        assert task["status"] == "completed"
        assert task["result"] == "Done"
        assert task["completed_at"] is not None

    async def test_create_and_get_goal(self, state):
        goal_id = await state.create_goal("Build landing page", plan_path="/tmp/plan.md")
        goal = await state.get_goal(goal_id)
        assert goal is not None
        assert goal["description"] == "Build landing page"
        assert goal["status"] == "planning"
        assert goal["plan_path"] == "/tmp/plan.md"

    async def test_update_goal_status(self, state):
        goal_id = await state.create_goal("Build feature", plan_path="/tmp/plan.md")
        await state.update_goal(goal_id, status="executing")
        goal = await state.get_goal(goal_id)
        assert goal["status"] == "executing"

    async def test_update_goal_plan_path(self, state):
        goal_id = await state.create_goal("Build feature", plan_path="")
        await state.update_goal_plan_path(goal_id, "/tmp/real-plan.md")
        goal = await state.get_goal(goal_id)
        assert goal["plan_path"] == "/tmp/real-plan.md"

    async def test_record_and_list_executions(self, state):
        goal_id = await state.create_goal("Goal", plan_path="/tmp/p.md")
        await state.record_execution(
            goal_id=goal_id,
            task_id=None,
            subtask="Build API",
            employee_id="backend-engineer",
            attempt=1,
        )
        execs = await state.list_executions(goal_id=goal_id)
        assert len(execs) == 1
        assert execs[0]["subtask"] == "Build API"
        assert execs[0]["status"] == "running"

    async def test_update_execution(self, state):
        goal_id = await state.create_goal("Goal", plan_path="/tmp/p.md")
        exec_id = await state.record_execution(
            goal_id=goal_id,
            task_id=None,
            subtask="Build API",
            employee_id="backend-engineer",
            attempt=1,
        )
        await state.update_execution(exec_id, status="completed", output="Done building API")
        execs = await state.list_executions(goal_id=goal_id)
        assert execs[0]["status"] == "completed"
        assert execs[0]["output"] == "Done building API"
        assert execs[0]["finished_at"] is not None

    async def test_list_all_status(self, state):
        await state.create_task("Task 1")
        await state.create_goal("Goal 1", plan_path="/tmp/p.md")
        items = await state.list_all_status()
        assert len(items) == 2

    async def test_check_constraint_on_execution(self, state):
        """Both goal_id and task_id cannot be NULL."""
        with pytest.raises(Exception):
            await state.record_execution(
                goal_id=None,
                task_id=None,
                subtask="Orphan",
                employee_id="nobody",
                attempt=1,
            )
