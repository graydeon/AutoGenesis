# CEO Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the CEO Orchestrator that decomposes high-level goals into subtasks, assigns them to employees via LLM reasoning, dispatches via SubAgentManager, and adapts the plan based on results.

**Architecture:** `CEOOrchestrator` coordinates between `EmployeeRegistry` (roster), `EmployeeRuntime` (system prompts), `SubAgentManager` (dispatch), and `CodexClient` (reasoning). State lives in SQLite (`ceo.db`) + markdown plans. CLI exposes `ceo` subcommand group.

**Tech Stack:** Python 3.11+, aiosqlite, pydantic, structlog, typer, rich, pytest-asyncio

**Spec:** `docs/superpowers/specs/2026-03-19-ceo-orchestrator-design.md`

---

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `packages/employees/src/autogenesis_employees/ceo_models.py` | Data models: ManagerBundle, SubtaskResult, GoalResult, TaskResult, GoalStatus, TaskStatus |
| `packages/employees/src/autogenesis_employees/state.py` | CEOStateManager — async SQLite CRUD for ceo.db (tasks, goals, executions tables) |
| `packages/employees/src/autogenesis_employees/reasoning.py` | JSON extraction + three LLM reasoning call builders (decompose, assign, re-evaluate) |
| `packages/employees/src/autogenesis_employees/orchestrator.py` | CEOOrchestrator — the run loop, enqueue, dispatch, resume, status, close |
| `packages/cli/src/autogenesis_cli/commands/ceo.py` | Typer sub-app: enqueue, run, dispatch, status, plan, resume |
| `packages/employees/tests/test_ceo_models.py` | Tests for CEO data models |
| `packages/employees/tests/test_state.py` | Tests for CEOStateManager |
| `packages/employees/tests/test_reasoning.py` | Tests for JSON extraction and reasoning prompt builders |
| `packages/employees/tests/test_orchestrator.py` | Tests for CEOOrchestrator (mocked CodexClient + SubAgentManager) |

### Modified Files

| File | Change |
|------|--------|
| `packages/core/src/autogenesis_core/events.py` | Add 6 CEO event types |
| `packages/core/src/autogenesis_core/config.py` | Add `dispatch_timeout` to EmployeesConfig |
| `packages/cli/src/autogenesis_cli/app.py` | Register `ceo_app` sub-typer |
| `packages/core/tests/test_events.py` | Update event count assertion |
| `packages/core/tests/test_config.py` | Test dispatch_timeout field |

---

### Task 1: CEO Data Models

**Files:**
- Create: `packages/employees/src/autogenesis_employees/ceo_models.py`
- Test: `packages/employees/tests/test_ceo_models.py`

- [ ] **Step 1: Write the failing tests**

```python
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
        # Will fail because ceo_models.py doesn't exist yet
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/gray/dev/AutoGenesis && python -m pytest packages/employees/tests/test_ceo_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'autogenesis_employees.ceo_models'`

- [ ] **Step 3: Write the implementation**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/gray/dev/AutoGenesis && python -m pytest packages/employees/tests/test_ceo_models.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add packages/employees/src/autogenesis_employees/ceo_models.py packages/employees/tests/test_ceo_models.py
git commit -m "feat(ceo): add CEO orchestrator data models"
```

---

### Task 2: Config + Events Updates

**Files:**
- Modify: `packages/core/src/autogenesis_core/config.py:66-77` — add `dispatch_timeout` to EmployeesConfig
- Modify: `packages/core/src/autogenesis_core/events.py:20-58` — add 6 CEO event types
- Modify: `packages/core/tests/test_events.py` — update event count
- Modify: `packages/core/tests/test_config.py` — test new field

- [ ] **Step 1: Write the failing tests**

Add to existing test files:

In `packages/core/tests/test_config.py`, add:
```python
def test_employees_config_dispatch_timeout():
    """EmployeesConfig has dispatch_timeout defaulting to 300."""
    from autogenesis_core.config import EmployeesConfig

    cfg = EmployeesConfig()
    assert cfg.dispatch_timeout == 300.0
```

In `packages/core/tests/test_events.py`, update the test:
1. Rename `test_all_36_event_types_exist` to `test_all_42_event_types_exist`
2. Add these 6 values to the `expected` set:
```python
            "ceo.goal.start",
            "ceo.subtask.assign",
            "ceo.subtask.complete",
            "ceo.subtask.fail",
            "ceo.escalation",
            "ceo.goal.complete",
```
3. Change `assert len(EventType) == 36` to `assert len(EventType) == 42`

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/gray/dev/AutoGenesis && python -m pytest packages/core/tests/test_config.py::test_employees_config_dispatch_timeout -v`
Expected: FAIL — `dispatch_timeout` field doesn't exist yet

- [ ] **Step 3: Add dispatch_timeout to EmployeesConfig**

In `packages/core/src/autogenesis_core/config.py`, add to `EmployeesConfig`:
```python
    dispatch_timeout: float = 300.0
```

- [ ] **Step 4: Add 6 CEO event types to EventType**

In `packages/core/src/autogenesis_core/events.py`, add after `EMPLOYEE_UNION_PROPOSAL`:
```python
    CEO_GOAL_START = "ceo.goal.start"
    CEO_SUBTASK_ASSIGN = "ceo.subtask.assign"
    CEO_SUBTASK_COMPLETE = "ceo.subtask.complete"
    CEO_SUBTASK_FAIL = "ceo.subtask.fail"
    CEO_ESCALATION = "ceo.escalation"
    CEO_GOAL_COMPLETE = "ceo.goal.complete"
```

Update the docstring from `"""36 event types` to `"""42 event types`.

- [ ] **Step 5: Update event count assertion in test**

In `packages/core/tests/test_events.py`, find the assertion `assert len(EventType) == 36` and change to `assert len(EventType) == 42`.

- [ ] **Step 6: Run all core tests**

Run: `cd /home/gray/dev/AutoGenesis && python -m pytest packages/core/tests/ -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add packages/core/src/autogenesis_core/config.py packages/core/src/autogenesis_core/events.py packages/core/tests/
git commit -m "feat(ceo): add dispatch_timeout config and CEO event types"
```

---

### Task 3: CEOStateManager

**Files:**
- Create: `packages/employees/src/autogenesis_employees/state.py`
- Test: `packages/employees/tests/test_state.py`

This is the SQLite CRUD layer for `ceo.db` with three tables: tasks, goals, executions.

- [ ] **Step 1: Write the failing tests**

```python
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
        # Higher priority first
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

    async def test_record_and_list_executions(self, state):
        goal_id = await state.create_goal("Goal", plan_path="/tmp/p.md")
        exec_id = await state.record_execution(
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
        with pytest.raises(Exception):  # noqa: B017
            await state.record_execution(
                goal_id=None,
                task_id=None,
                subtask="Orphan",
                employee_id="nobody",
                attempt=1,
            )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/gray/dev/AutoGenesis && python -m pytest packages/employees/tests/test_state.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'autogenesis_employees.state'`

- [ ] **Step 3: Write the implementation**

```python
"""CEOStateManager — async SQLite CRUD for ceo.db.

Three tables: tasks (queue), goals (decomposition tracking), executions (dispatch log).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import aiosqlite
import structlog

if TYPE_CHECKING:
    from pathlib import Path

logger = structlog.get_logger()

_CREATE_TASKS = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    result TEXT
)
"""

_CREATE_GOALS = """
CREATE TABLE IF NOT EXISTS goals (
    id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    plan_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'planning',
    created_at TEXT NOT NULL,
    completed_at TEXT
)
"""

_CREATE_EXECUTIONS = """
CREATE TABLE IF NOT EXISTS executions (
    id TEXT PRIMARY KEY,
    goal_id TEXT,
    task_id TEXT,
    subtask TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    attempt INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'running',
    output TEXT DEFAULT '',
    started_at TEXT NOT NULL,
    finished_at TEXT,
    CHECK (goal_id IS NOT NULL OR task_id IS NOT NULL)
)
"""


class CEOStateManager:
    """Async SQLite state for the CEO orchestrator."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute(_CREATE_TASKS)
        await self._db.execute(_CREATE_GOALS)
        await self._db.execute(_CREATE_EXECUTIONS)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    def _require_db(self) -> aiosqlite.Connection:
        if self._db is None:
            msg = "CEOStateManager not initialized"
            raise RuntimeError(msg)
        return self._db

    # --- Tasks ---

    async def create_task(self, description: str, priority: int = 0) -> str:
        db = self._require_db()
        task_id = uuid4().hex[:16]
        now = datetime.now(UTC).isoformat()
        await db.execute(
            "INSERT INTO tasks (id, description, priority, created_at) VALUES (?, ?, ?, ?)",
            (task_id, description, priority, now),
        )
        await db.commit()
        return task_id

    async def get_task(self, task_id: str) -> dict[str, Any] | None:
        db = self._require_db()
        cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def list_pending_tasks(self) -> list[dict[str, Any]]:
        db = self._require_db()
        cursor = await db.execute(
            "SELECT * FROM tasks WHERE status = 'pending' ORDER BY priority DESC, created_at ASC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def update_task(
        self, task_id: str, status: str | None = None, result: str | None = None
    ) -> None:
        db = self._require_db()
        updates: list[str] = []
        params: list[Any] = []
        if status is not None:
            updates.append("status = ?")
            params.append(status)
            if status in ("completed", "failed", "escalated"):
                updates.append("completed_at = ?")
                params.append(datetime.now(UTC).isoformat())
        if result is not None:
            updates.append("result = ?")
            params.append(result)
        if updates:
            params.append(task_id)
            await db.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", params)
            await db.commit()

    # --- Goals ---

    async def create_goal(self, description: str, plan_path: str) -> str:
        db = self._require_db()
        goal_id = uuid4().hex[:16]
        now = datetime.now(UTC).isoformat()
        await db.execute(
            "INSERT INTO goals (id, description, plan_path, created_at) VALUES (?, ?, ?, ?)",
            (goal_id, description, plan_path, now),
        )
        await db.commit()
        return goal_id

    async def get_goal(self, goal_id: str) -> dict[str, Any] | None:
        db = self._require_db()
        cursor = await db.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def update_goal_plan_path(self, goal_id: str, plan_path: str) -> None:
        db = self._require_db()
        await db.execute("UPDATE goals SET plan_path = ? WHERE id = ?", (plan_path, goal_id))
        await db.commit()

    async def update_goal(
        self, goal_id: str, status: str | None = None
    ) -> None:
        db = self._require_db()
        updates: list[str] = []
        params: list[Any] = []
        if status is not None:
            updates.append("status = ?")
            params.append(status)
            if status in ("completed", "failed", "escalated"):
                updates.append("completed_at = ?")
                params.append(datetime.now(UTC).isoformat())
        if updates:
            params.append(goal_id)
            await db.execute(f"UPDATE goals SET {', '.join(updates)} WHERE id = ?", params)
            await db.commit()

    # --- Executions ---

    async def record_execution(
        self,
        goal_id: str | None,
        task_id: str | None,
        subtask: str,
        employee_id: str,
        attempt: int = 1,
    ) -> str:
        db = self._require_db()
        exec_id = uuid4().hex[:16]
        now = datetime.now(UTC).isoformat()
        await db.execute(
            "INSERT INTO executions (id, goal_id, task_id, subtask, employee_id, attempt, started_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (exec_id, goal_id, task_id, subtask, employee_id, attempt, now),
        )
        await db.commit()
        return exec_id

    async def update_execution(
        self, exec_id: str, status: str | None = None, output: str | None = None
    ) -> None:
        db = self._require_db()
        updates: list[str] = []
        params: list[Any] = []
        if status is not None:
            updates.append("status = ?")
            params.append(status)
            if status in ("completed", "failed", "timed_out"):
                updates.append("finished_at = ?")
                params.append(datetime.now(UTC).isoformat())
        if output is not None:
            updates.append("output = ?")
            params.append(output)
        if updates:
            params.append(exec_id)
            await db.execute(f"UPDATE executions SET {', '.join(updates)} WHERE id = ?", params)
            await db.commit()

    async def list_executions(self, goal_id: str | None = None, task_id: str | None = None) -> list[dict[str, Any]]:
        db = self._require_db()
        if goal_id:
            cursor = await db.execute(
                "SELECT * FROM executions WHERE goal_id = ? ORDER BY started_at ASC", (goal_id,)
            )
        elif task_id:
            cursor = await db.execute(
                "SELECT * FROM executions WHERE task_id = ? ORDER BY started_at ASC", (task_id,)
            )
        else:
            cursor = await db.execute("SELECT * FROM executions ORDER BY started_at ASC")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # --- Status ---

    async def list_all_status(self) -> list[dict[str, Any]]:
        db = self._require_db()
        items: list[dict[str, Any]] = []
        cursor = await db.execute("SELECT * FROM goals ORDER BY created_at DESC")
        for row in await cursor.fetchall():
            items.append({**dict(row), "type": "goal"})
        cursor = await db.execute("SELECT * FROM tasks ORDER BY priority DESC, created_at DESC")
        for row in await cursor.fetchall():
            items.append({**dict(row), "type": "task"})
        return items
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/gray/dev/AutoGenesis && python -m pytest packages/employees/tests/test_state.py -v`
Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add packages/employees/src/autogenesis_employees/state.py packages/employees/tests/test_state.py
git commit -m "feat(ceo): add CEOStateManager — SQLite CRUD for task queue, goals, executions"
```

---

### Task 4: Reasoning Module (JSON extraction + prompt builders)

**Files:**
- Create: `packages/employees/src/autogenesis_employees/reasoning.py`
- Test: `packages/employees/tests/test_reasoning.py`

This module contains the JSON extraction utility and three functions that build the messages/instructions for each Codex reasoning call (decompose, assign, re-evaluate). It does NOT call CodexClient — that's the orchestrator's job. This module is pure logic.

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for CEO reasoning — JSON extraction and prompt builders."""

from __future__ import annotations

import json

import pytest

from autogenesis_employees.reasoning import (
    build_assign_prompt,
    build_decompose_prompt,
    build_reevaluate_prompt,
    extract_json,
)


class TestExtractJson:
    def test_fenced_json_block(self):
        text = 'Here is the result:\n```json\n[{"description": "task 1"}]\n```\nDone.'
        result = extract_json(text)
        assert result == [{"description": "task 1"}]

    def test_raw_json_array(self):
        text = 'The tasks are: [{"description": "task 1"}, {"description": "task 2"}]'
        result = extract_json(text)
        assert len(result) == 2

    def test_raw_json_object(self):
        text = 'Result: {"employee_id": "backend-engineer", "reasoning": "best fit"}'
        result = extract_json(text)
        assert result["employee_id"] == "backend-engineer"

    def test_no_json_raises(self):
        with pytest.raises(ValueError, match="No JSON"):
            extract_json("This has no JSON in it at all.")

    def test_no_changes_object(self):
        text = '```json\n{"no_changes": true}\n```'
        result = extract_json(text)
        assert result["no_changes"] is True

    def test_multiline_fenced(self):
        text = '```json\n[\n  {"description": "a", "rationale": "b"},\n  {"description": "c", "rationale": "d"}\n]\n```'
        result = extract_json(text)
        assert len(result) == 2


class TestBuildDecomposePrompt:
    def test_returns_instructions_and_message(self):
        roster = [
            {"id": "be", "title": "Backend Engineer", "persona": "Writes APIs", "tools": ["shell"]},
        ]
        instructions, message = build_decompose_prompt(
            goal="Build user auth",
            roster_summary=roster,
            changelog_entries=["## 2026-03-19 — cto\n**Task:** setup"],
        )
        assert "CEO" in instructions
        assert "Build user auth" in message
        assert "Backend Engineer" in message
        # Verify the instructions ask for JSON output
        assert "JSON" in instructions

    def test_empty_changelog(self):
        instructions, message = build_decompose_prompt(
            goal="Build feature",
            roster_summary=[],
            changelog_entries=[],
        )
        assert "Build feature" in message


class TestBuildAssignPrompt:
    def test_returns_instructions_and_message(self):
        roster = [
            {"id": "be", "title": "Backend Engineer", "persona": "APIs", "tools": ["shell"], "training_directives": []},
        ]
        instructions, message = build_assign_prompt(
            subtask="Build REST endpoint",
            goal_context="Building user auth",
            roster_details=roster,
            previous_results=[],
        )
        assert "pick the single best employee" in instructions.lower() or "best employee" in instructions.lower()
        assert "Build REST endpoint" in message
        assert "Building user auth" in message

    def test_with_previous_results(self):
        instructions, message = build_assign_prompt(
            subtask="Write tests",
            goal_context="Building user auth",
            roster_details=[],
            previous_results=[{"subtask": "Build API", "result": "Done"}],
        )
        assert "Build API" in message


class TestBuildReevaluatePrompt:
    def test_returns_instructions_and_message(self):
        instructions, message = build_reevaluate_prompt(
            goal="Build user auth",
            plan_markdown="## Subtasks\n- [x] Build API\n- [ ] Write tests",
            latest_result="API complete",
        )
        assert "Review" in instructions or "review" in instructions
        assert "Build user auth" in message
        assert "API complete" in message
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/gray/dev/AutoGenesis && python -m pytest packages/employees/tests/test_reasoning.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

```python
"""CEO reasoning — JSON extraction and prompt builders for Codex calls.

Three reasoning calls:
1. Decompose: goal → ordered subtasks
2. Assign: subtask → employee pick
3. Re-evaluate: completed work → updated plan

Each builder returns (instructions: str, user_message: str) to pass to
CodexClient.create_response_sync().
"""

from __future__ import annotations

import json
import re
from typing import Any

_FENCED_JSON_RE = re.compile(r"```(?:json)?\s*\n([\s\S]*?)\n```", re.MULTILINE)


def extract_json(text: str) -> Any:
    """Extract first JSON array or object from text.

    Tries fenced ```json blocks first, then scans for raw JSON.
    Raises ValueError if no valid JSON found.
    """
    # Try fenced blocks
    match = _FENCED_JSON_RE.search(text)
    if match:
        return json.loads(match.group(1).strip())

    # Try raw JSON: find first [ or {
    for i, ch in enumerate(text):
        if ch in ("[", "{"):
            try:
                return json.loads(text[i:])
            except json.JSONDecodeError:
                # Try to find balanced end
                depth = 0
                close = "]" if ch == "[" else "}"
                for j in range(i, len(text)):
                    if text[j] == ch:
                        depth += 1
                    elif text[j] == close:
                        depth -= 1
                        if depth == 0:
                            try:
                                return json.loads(text[i : j + 1])
                            except json.JSONDecodeError:
                                break
                continue

    msg = "No JSON found in text"
    raise ValueError(msg)


def build_decompose_prompt(
    goal: str,
    roster_summary: list[dict[str, Any]],
    changelog_entries: list[str],
) -> tuple[str, str]:
    """Build the decompose reasoning call.

    Returns (instructions, user_message).
    """
    instructions = (
        "You are the CEO of a software startup. Decompose the given goal into concrete, "
        "ordered subtasks. Each subtask should be completable by one employee in one session. "
        "Consider the available team and their capabilities.\n\n"
        "Respond with ONLY a JSON array of objects: "
        '[{"description": "...", "rationale": "..."}]'
    )

    parts = [f"## Goal\n\n{goal}\n"]

    if roster_summary:
        parts.append("## Available Team\n")
        for emp in roster_summary:
            tools_str = ", ".join(emp.get("tools", []))
            parts.append(f"- **{emp['title']}** (id: {emp['id']}): {emp.get('persona', '')}. Tools: {tools_str}")
        parts.append("")

    if changelog_entries:
        parts.append("## Recent Activity\n")
        parts.extend(changelog_entries[:5])
        parts.append("")

    return instructions, "\n".join(parts)


def build_assign_prompt(
    subtask: str,
    goal_context: str,
    roster_details: list[dict[str, Any]],
    previous_results: list[dict[str, Any]],
) -> tuple[str, str]:
    """Build the assign reasoning call.

    Returns (instructions, user_message).
    """
    instructions = (
        "Given a subtask and available employees, pick the single best employee to handle it. "
        "Consider their tools, training, and expertise.\n\n"
        'Respond with ONLY a JSON object: {"employee_id": "...", "reasoning": "..."}'
    )

    parts = [f"## Overall Goal\n\n{goal_context}\n", f"## Current Subtask\n\n{subtask}\n"]

    if roster_details:
        parts.append("## Available Employees\n")
        for emp in roster_details:
            tools_str = ", ".join(emp.get("tools", []))
            directives = emp.get("training_directives", [])
            directives_str = "; ".join(directives) if directives else "none"
            parts.append(
                f"- **{emp.get('title', emp['id'])}** (id: {emp['id']}): "
                f"{emp.get('persona', '')}. Tools: {tools_str}. Training: {directives_str}"
            )
        parts.append("")

    if previous_results:
        parts.append("## Previous Subtask Results\n")
        for prev in previous_results:
            parts.append(f"- {prev['subtask']}: {prev.get('result', 'no output')}")
        parts.append("")

    return instructions, "\n".join(parts)


def build_reevaluate_prompt(
    goal: str,
    plan_markdown: str,
    latest_result: str,
) -> tuple[str, str]:
    """Build the re-evaluate reasoning call.

    Returns (instructions, user_message).
    """
    instructions = (
        "Review the implementation plan in light of the latest completed work. "
        "Should remaining subtasks be changed, added, removed, or reordered? "
        "If no changes needed, respond with: {\"no_changes\": true}\n"
        "Otherwise respond with a JSON array of updated remaining subtasks: "
        '[{"description": "..."}]'
    )

    parts = [
        f"## Goal\n\n{goal}\n",
        f"## Current Plan\n\n{plan_markdown}\n",
        f"## Latest Completed Result\n\n{latest_result}\n",
    ]

    return instructions, "\n".join(parts)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/gray/dev/AutoGenesis && python -m pytest packages/employees/tests/test_reasoning.py -v`
Expected: All 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add packages/employees/src/autogenesis_employees/reasoning.py packages/employees/tests/test_reasoning.py
git commit -m "feat(ceo): add reasoning module — JSON extraction and prompt builders"
```

---

### Task 5: CEOOrchestrator

**Files:**
- Create: `packages/employees/src/autogenesis_employees/orchestrator.py`
- Test: `packages/employees/tests/test_orchestrator.py`

This is the main class. It integrates all components. Tests use mocked `CodexClient` and `SubAgentManager`.

**Important context for the implementer:**
- `CodexClient.create_response_sync(messages, instructions)` is an async method returning `CompletionResult` with a `.text` field
- `Message` is from `autogenesis_core.models` with `role` and `content` fields
- `SubAgentManager.spawn(task, cwd, timeout, system_prompt, env_overrides)` returns `SubAgentResult` with `output`, `exit_code`, `timed_out`, `success` (property)
- `EmployeeRegistry.list_active()` returns `list[EmployeeConfig]`
- `EmployeeRuntime.build_system_prompt(config, brain_context, inbox_messages, changelog_entries, task)` returns `str`
- `BrainManager.top_memories(limit)` returns `list[Memory]` — extract `.content` for `brain_context`
- `InboxManager.get_unread(employee_id)` returns `list[InboxMessage]` — format as `f"From {m.from_employee}: {m.subject}\n{m.body}"`
- `ChangelogManager.read_recent(limit)` returns `list[str]`
- Project root: walk up from cwd looking for `.autogenesis/` directory; fallback to cwd

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for CEOOrchestrator — the core run loop with mocked dependencies."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autogenesis_employees.orchestrator import CEOOrchestrator


def _mock_codex_result(text: str):
    """Create a mock CompletionResult with .text."""
    result = MagicMock()
    result.text = text
    return result


def _mock_spawn_success(output: str = "Done"):
    """Create a mock SubAgentResult for success."""
    result = MagicMock()
    result.output = output
    result.exit_code = 0
    result.timed_out = False
    result.success = True
    return result


def _mock_spawn_failure(output: str = "Error occurred"):
    """Create a mock SubAgentResult for failure."""
    result = MagicMock()
    result.output = output
    result.exit_code = 1
    result.timed_out = False
    result.success = False
    return result


@pytest.fixture
def mock_deps(tmp_path):
    """Create mocked dependencies for CEOOrchestrator."""
    # Mock EmployeeRegistry
    registry = MagicMock()
    emp = MagicMock()
    emp.id = "backend-engineer"
    emp.title = "Backend Engineer"
    emp.persona = "Writes APIs"
    emp.tools = ["shell"]
    emp.training_directives = []
    emp.env = {}
    emp.model_dump.return_value = {
        "id": "backend-engineer",
        "title": "Backend Engineer",
        "persona": "Writes APIs",
        "tools": ["shell"],
        "training_directives": [],
    }
    registry.list_active.return_value = [emp]
    registry.get.return_value = emp

    # Mock EmployeeRuntime
    runtime = MagicMock()
    runtime.build_system_prompt.return_value = "You are Backend Engineer..."

    # Mock SubAgentManager
    sub_agent_mgr = MagicMock()
    sub_agent_mgr.spawn = AsyncMock(return_value=_mock_spawn_success())

    # Mock CodexClient
    codex = MagicMock()
    codex.create_response_sync = AsyncMock()

    return {
        "registry": registry,
        "runtime": runtime,
        "sub_agent_mgr": sub_agent_mgr,
        "codex": codex,
        "base_dir": tmp_path / ".autogenesis",
    }


class TestCEOOrchestrator:
    async def test_enqueue_and_status(self, mock_deps):
        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        task_id = await orch.enqueue("Fix login bug", priority=5)
        assert task_id is not None
        items = await orch.status()
        assert len(items) >= 1
        await orch.close()

    async def test_run_single_subtask_goal(self, mock_deps):
        codex = mock_deps["codex"]
        # Decompose: returns single subtask
        decompose_json = json.dumps([{"description": "Build the endpoint", "rationale": "Only task"}])
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best fit"})
        reevaluate_json = json.dumps({"no_changes": True})

        codex.create_response_sync = AsyncMock(
            side_effect=[
                _mock_codex_result(decompose_json),
                _mock_codex_result(assign_json),
                _mock_codex_result(reevaluate_json),
            ]
        )

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        result = await orch.run("Build user auth")
        assert result.status == "completed"
        assert len(result.subtask_results) == 1
        assert result.subtask_results[0].employee_id == "backend-engineer"
        await orch.close()

    async def test_run_with_retry_on_failure(self, mock_deps):
        codex = mock_deps["codex"]
        sub = mock_deps["sub_agent_mgr"]

        decompose_json = json.dumps([{"description": "Build API"}])
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})
        reevaluate_json = json.dumps({"no_changes": True})

        codex.create_response_sync = AsyncMock(
            side_effect=[
                _mock_codex_result(decompose_json),
                _mock_codex_result(assign_json),
                _mock_codex_result(reevaluate_json),
            ]
        )

        # First call fails, second succeeds (retry)
        sub.spawn = AsyncMock(
            side_effect=[_mock_spawn_failure(), _mock_spawn_success()]
        )

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        result = await orch.run("Build API")
        assert result.status == "completed"
        assert sub.spawn.call_count == 2  # Original + 1 retry
        await orch.close()

    async def test_run_escalation_after_two_failures(self, mock_deps):
        codex = mock_deps["codex"]
        sub = mock_deps["sub_agent_mgr"]

        decompose_json = json.dumps([{"description": "Build API"}])
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})

        codex.create_response_sync = AsyncMock(
            side_effect=[
                _mock_codex_result(decompose_json),
                _mock_codex_result(assign_json),
            ]
        )

        # Both attempts fail
        sub.spawn = AsyncMock(return_value=_mock_spawn_failure())

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        result = await orch.run("Build API")
        assert result.status == "escalated"
        assert sub.spawn.call_count == 2
        await orch.close()

    async def test_dispatch_standalone_task(self, mock_deps):
        codex = mock_deps["codex"]
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})
        codex.create_response_sync = AsyncMock(return_value=_mock_codex_result(assign_json))

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        task_id = await orch.enqueue("Fix bug")
        result = await orch.dispatch(task_id)
        assert result.status == "completed"
        assert result.employee_id == "backend-engineer"
        await orch.close()

    async def test_dispatch_next_from_queue(self, mock_deps):
        codex = mock_deps["codex"]
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})
        codex.create_response_sync = AsyncMock(return_value=_mock_codex_result(assign_json))

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        await orch.enqueue("Low priority", priority=1)
        await orch.enqueue("High priority", priority=10)
        result = await orch.dispatch()
        # Should dispatch highest priority
        assert result.task_id is not None
        await orch.close()

    async def test_empty_roster_raises(self, mock_deps):
        mock_deps["registry"].list_active.return_value = []
        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        with pytest.raises(RuntimeError, match="No active employees"):
            await orch.run("Build something")
        await orch.close()

    async def test_resume_continues_from_escalated(self, mock_deps):
        codex = mock_deps["codex"]
        sub = mock_deps["sub_agent_mgr"]

        decompose_json = json.dumps([{"description": "Step 1"}, {"description": "Step 2"}])
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})
        reevaluate_json = json.dumps({"no_changes": True})

        # First run: Step 1 succeeds, Step 2 fails → escalation
        codex.create_response_sync = AsyncMock(
            side_effect=[
                _mock_codex_result(decompose_json),
                _mock_codex_result(assign_json),
                _mock_codex_result(reevaluate_json),
                _mock_codex_result(assign_json),  # assign Step 2
            ]
        )
        sub.spawn = AsyncMock(
            side_effect=[_mock_spawn_success(), _mock_spawn_failure(), _mock_spawn_failure()]
        )

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        result = await orch.run("Two steps")
        assert result.status == "escalated"
        goal_id = result.goal_id

        # Resume: Step 2 now succeeds
        codex.create_response_sync = AsyncMock(
            side_effect=[
                _mock_codex_result(assign_json),
                _mock_codex_result(reevaluate_json),
            ]
        )
        sub.spawn = AsyncMock(return_value=_mock_spawn_success())
        resumed = await orch.resume(goal_id)
        assert resumed.status == "completed"
        assert resumed.goal_id == goal_id
        await orch.close()

    async def test_plan_markdown_created(self, mock_deps):
        codex = mock_deps["codex"]
        decompose_json = json.dumps([{"description": "Step 1"}, {"description": "Step 2"}])
        assign_json = json.dumps({"employee_id": "backend-engineer", "reasoning": "best"})
        reevaluate_json = json.dumps({"no_changes": True})

        codex.create_response_sync = AsyncMock(
            side_effect=[
                _mock_codex_result(decompose_json),
                _mock_codex_result(assign_json),
                _mock_codex_result(reevaluate_json),
                _mock_codex_result(assign_json),
                _mock_codex_result(reevaluate_json),
            ]
        )

        orch = CEOOrchestrator(**mock_deps)
        await orch.initialize()
        result = await orch.run("Two step goal")
        plan_path = Path(result.plan_path)
        assert plan_path.exists()
        content = plan_path.read_text()
        assert "Step 1" in content
        assert "Step 2" in content
        await orch.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/gray/dev/AutoGenesis && python -m pytest packages/employees/tests/test_orchestrator.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

Create `packages/employees/src/autogenesis_employees/orchestrator.py`:

```python
"""CEOOrchestrator — the central brain of the agent employee system.

Decomposes goals into subtasks, assigns employees via LLM reasoning,
dispatches via SubAgentManager, and adapts plans based on results.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from autogenesis_core.events import Event, EventType, get_event_bus
from autogenesis_core.models import Message
from autogenesis_employees.ceo_models import (
    GoalResult,
    GoalStatus,
    ManagerBundle,
    SubtaskResult,
    TaskResult,
    TaskStatus,
)
from autogenesis_employees.reasoning import (
    build_assign_prompt,
    build_decompose_prompt,
    build_reevaluate_prompt,
    extract_json,
)
from autogenesis_employees.state import CEOStateManager

if TYPE_CHECKING:
    from autogenesis_core.client import CodexClient
    from autogenesis_core.sub_agents import SubAgentManager
    from autogenesis_employees.changelog import ChangelogManager
    from autogenesis_employees.registry import EmployeeRegistry
    from autogenesis_employees.runtime import EmployeeRuntime

logger = structlog.get_logger()


def _find_project_root() -> Path:
    """Walk up from cwd looking for .autogenesis/ directory."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".autogenesis").is_dir():
            return parent
    return cwd


class CEOOrchestrator:
    """Coordinates employee dispatch for goals and standalone tasks."""

    def __init__(
        self,
        registry: EmployeeRegistry,
        runtime: EmployeeRuntime,
        sub_agent_mgr: SubAgentManager,
        codex: CodexClient,
        base_dir: Path | None = None,
        dispatch_timeout: float = 300.0,
    ) -> None:
        self._registry = registry
        self._runtime = runtime
        self._sub_agent_mgr = sub_agent_mgr
        self._codex = codex
        self._dispatch_timeout = dispatch_timeout
        self._project_root = _find_project_root()
        self._base_dir = base_dir or (self._project_root / ".autogenesis")
        self._state: CEOStateManager | None = None
        self._changelog: ChangelogManager | None = None
        self._managers: dict[str, ManagerBundle] = {}
        self._bus = get_event_bus()

    async def initialize(self) -> None:
        """Initialize state DB and changelog."""
        from autogenesis_employees.changelog import ChangelogManager

        ceo_dir = self._base_dir / "ceo"
        ceo_dir.mkdir(parents=True, exist_ok=True)
        (ceo_dir / "plans").mkdir(exist_ok=True)

        self._state = CEOStateManager(db_path=ceo_dir / "ceo.db")
        await self._state.initialize()

        self._changelog = ChangelogManager(self._base_dir / "changelog.md")

    async def close(self) -> None:
        """Close all manager connections and state DB."""
        for bundle in self._managers.values():
            await bundle.brain.close()
            await bundle.inbox.close()
        self._managers.clear()
        if self._state:
            await self._state.close()

    def _require_state(self) -> CEOStateManager:
        if self._state is None:
            msg = "CEOOrchestrator not initialized"
            raise RuntimeError(msg)
        return self._state

    # --- Manager lifecycle ---

    async def _get_managers(self, employee_id: str) -> ManagerBundle:
        if employee_id not in self._managers:
            from autogenesis_employees.brain import BrainManager
            from autogenesis_employees.inbox import InboxManager

            data_dir = self._base_dir / "employees" / employee_id
            brain = BrainManager(data_dir / "brain.db")
            inbox = InboxManager(data_dir / "inbox.db")
            await brain.initialize()
            await inbox.initialize()
            self._managers[employee_id] = ManagerBundle(brain=brain, inbox=inbox)
        return self._managers[employee_id]

    # --- Roster helpers ---

    def _check_roster(self) -> None:
        if not self._registry.list_active():
            msg = "No active employees — use `autogenesis hr hire` to add employees"
            raise RuntimeError(msg)

    def _roster_summary(self) -> list[dict[str, Any]]:
        return [
            {
                "id": e.id,
                "title": e.title,
                "persona": e.persona,
                "tools": e.tools,
                "training_directives": e.training_directives,
            }
            for e in self._registry.list_active()
        ]

    # --- LLM calls ---

    async def _codex_call(self, instructions: str, user_message: str) -> str:
        """Make a reasoning call to Codex and return the text."""
        messages = [Message(role="user", content=user_message)]
        result = await self._codex.create_response_sync(messages, instructions=instructions)
        return result.text

    async def _codex_call_json(self, instructions: str, user_message: str) -> Any:
        """Make a reasoning call and extract JSON. Retries once on parse failure."""
        text = await self._codex_call(instructions, user_message)
        try:
            return extract_json(text)
        except ValueError:
            # Retry with stricter instruction
            retry_instructions = instructions + "\n\nIMPORTANT: Respond with ONLY valid JSON. No other text."
            text = await self._codex_call(retry_instructions, user_message)
            return extract_json(text)

    # --- Context building ---

    async def _build_employee_context(self, employee_id: str, task: str) -> str:
        """Build system prompt for an employee dispatch."""
        config = self._registry.get(employee_id)
        if not config:
            msg = f"Employee {employee_id} not found"
            raise RuntimeError(msg)

        managers = await self._get_managers(employee_id)
        brain_context = [m.content for m in await managers.brain.top_memories(20)]
        inbox_messages = [
            f"From {m.from_employee}: {m.subject}\n{m.body}"
            for m in await managers.inbox.get_unread(employee_id)
        ]
        changelog_entries = self._changelog.read_recent(10) if self._changelog else []

        return self._runtime.build_system_prompt(
            config=config,
            brain_context=brain_context,
            inbox_messages=inbox_messages,
            changelog_entries=changelog_entries,
            task=task,
        )

    # --- Plan markdown ---

    def _write_plan(self, goal_id: str, goal: str, subtasks: list[dict[str, Any]]) -> Path:
        """Write initial plan markdown."""
        plan_path = self._base_dir / "ceo" / "plans" / f"goal-{goal_id}.md"
        lines = [f"# Goal: {goal}\n", f"Status: executing\n", "\n## Subtasks\n"]
        for i, st in enumerate(subtasks, 1):
            lines.append(f"- [ ] **{i}. {st['description']}**\n  (pending)\n")
        plan_path.write_text("\n".join(lines))
        return plan_path

    def _update_plan_subtask(self, plan_path: Path, index: int, employee_id: str, result_summary: str) -> None:
        """Mark a subtask as complete in the plan markdown."""
        content = plan_path.read_text()
        # Find the Nth checkbox and replace
        count = 0
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith("- [ ] **"):
                count += 1
                if count == index:
                    lines[i] = line.replace("- [ ]", "- [x]")
                    # Replace pending line
                    if i + 1 < len(lines) and "(pending)" in lines[i + 1]:
                        lines[i + 1] = f"  Assigned to: {employee_id}\n  Result: {result_summary}"
                    break
        plan_path.write_text("\n".join(lines))

    def _update_plan_status(self, plan_path: Path, status: str) -> None:
        content = plan_path.read_text()
        content = content.replace("Status: executing", f"Status: {status}")
        plan_path.write_text(content)

    def _rewrite_remaining_subtasks(self, plan_path: Path, completed_count: int, new_subtasks: list[dict[str, Any]]) -> None:
        """Replace remaining subtasks in plan after re-evaluation."""
        content = plan_path.read_text()
        lines = content.split("\n")
        # Find where remaining subtasks start (after completed ones)
        result_lines: list[str] = []
        completed_seen = 0
        in_subtasks = False
        for line in lines:
            if line.strip().startswith("- [x] **"):
                completed_seen += 1
                result_lines.append(line)
                in_subtasks = True
            elif line.strip().startswith("- [ ] **") and in_subtasks:
                break  # Skip old remaining subtasks
            else:
                if not in_subtasks or not line.strip().startswith(("(pending)", "Assigned to:", "Result:")):
                    result_lines.append(line)

        # Add new remaining subtasks
        for i, st in enumerate(new_subtasks, completed_count + 1):
            result_lines.append(f"- [ ] **{i}. {st['description']}**\n  (pending)\n")

        plan_path.write_text("\n".join(result_lines))

    # --- Dispatch ---

    async def _dispatch_employee(
        self,
        employee_id: str,
        task: str,
        failure_context: str | None = None,
    ) -> tuple[str, int, bool]:
        """Dispatch a single employee. Returns (output, exit_code, success)."""
        if failure_context:
            task_with_context = (
                f"{task}\n\n## Previous Attempt Failed\n\n{failure_context}\n"
                "Analyze what went wrong and try a different approach."
            )
        else:
            task_with_context = task

        system_prompt = await self._build_employee_context(employee_id, task_with_context)
        config = self._registry.get(employee_id)
        env_overrides = config.env if config else {}

        result = await self._sub_agent_mgr.spawn(
            task=task_with_context,
            cwd=str(self._project_root),
            timeout=self._dispatch_timeout,
            system_prompt=system_prompt,
            env_overrides=env_overrides,
        )
        return result.output, result.exit_code, result.success

    # --- Public API ---

    async def enqueue(self, description: str, priority: int = 0) -> str:
        """Push a task onto the queue. Returns task ID."""
        state = self._require_state()
        return await state.create_task(description, priority=priority)

    async def run(self, goal: str) -> GoalResult:
        """Decompose and execute a high-level goal."""
        state = self._require_state()
        self._check_roster()

        self._bus.emit(Event(event_type=EventType.CEO_GOAL_START, data={"goal": goal}))
        logger.info("ceo_goal_start", goal=goal[:100])

        # 1. Decompose
        roster = self._roster_summary()
        changelog = self._changelog.read_recent(5) if self._changelog else []
        instructions, message = build_decompose_prompt(goal, roster, changelog)
        subtasks_raw = await self._codex_call_json(instructions, message)
        if not isinstance(subtasks_raw, list) or not subtasks_raw:
            msg = "Decompose returned empty or invalid subtasks"
            raise RuntimeError(msg)

        # 2. Create goal record first, then write plan with real ID
        goal_id = await state.create_goal(goal, plan_path="")
        plan_path = self._write_plan(goal_id, goal, subtasks_raw)
        await state.update_goal_plan_path(goal_id, str(plan_path))
        await state.update_goal(goal_id, status="executing")

        # 3. Execute via rolling dispatch
        return await self._execute_plan(
            goal_id=goal_id, goal=goal, plan_path=plan_path,
            remaining=list(subtasks_raw), completed_count=0,
        )

    async def _execute_plan(
        self,
        goal_id: str,
        goal: str,
        plan_path: Path,
        remaining: list[dict[str, Any]],
        completed_count: int,
    ) -> GoalResult:
        """Rolling dispatch loop — shared by run() and resume()."""
        state = self._require_state()
        roster = self._roster_summary()
        subtask_results: list[SubtaskResult] = []

        # Gather previous results from executions table (for resume)
        prev_execs = await state.list_executions(goal_id=goal_id)
        previous_results = [
            {"subtask": e["subtask"], "result": (e.get("output") or "")[:200]}
            for e in prev_execs if e["status"] == "completed"
        ]

        while remaining:
            current = remaining.pop(0)
            subtask_desc = current["description"]
            completed_count += 1

            # Assign
            instructions, message = build_assign_prompt(
                subtask=subtask_desc,
                goal_context=goal,
                roster_details=roster,
                previous_results=previous_results,
            )
            assign_result = await self._codex_call_json(instructions, message)
            employee_id = assign_result.get("employee_id", "")
            if not self._registry.get(employee_id):
                employee_id = self._registry.list_active()[0].id

            self._bus.emit(Event(
                event_type=EventType.CEO_SUBTASK_ASSIGN,
                data={"subtask": subtask_desc, "employee_id": employee_id},
            ))
            logger.info("ceo_subtask_assign", subtask=subtask_desc[:80], employee=employee_id)

            # Dispatch with retry
            start_time = time.monotonic()
            output, exit_code, success = await self._dispatch_employee(employee_id, subtask_desc)
            attempt = 1

            exec_id = await state.record_execution(
                goal_id=goal_id, task_id=None, subtask=subtask_desc,
                employee_id=employee_id, attempt=attempt,
            )

            if not success:
                logger.warning("ceo_subtask_fail_retry", subtask=subtask_desc[:80], attempt=1)
                await state.update_execution(exec_id, status="failed", output=output)
                attempt = 2
                output, exit_code, success = await self._dispatch_employee(
                    employee_id, subtask_desc, failure_context=output
                )
                exec_id = await state.record_execution(
                    goal_id=goal_id, task_id=None, subtask=subtask_desc,
                    employee_id=employee_id, attempt=attempt,
                )

            duration = time.monotonic() - start_time

            if success:
                await state.update_execution(exec_id, status="completed", output=output)
                self._update_plan_subtask(plan_path, completed_count, employee_id, output[:200])
                self._bus.emit(Event(
                    event_type=EventType.CEO_SUBTASK_COMPLETE,
                    data={"subtask": subtask_desc, "employee_id": employee_id},
                ))
                subtask_results.append(SubtaskResult(
                    subtask=subtask_desc, employee_id=employee_id,
                    status="completed", output=output, attempt=attempt,
                    duration_seconds=duration,
                ))
                previous_results.append({"subtask": subtask_desc, "result": output[:200]})

                # Re-evaluate if more subtasks remain
                if remaining:
                    plan_text = plan_path.read_text()
                    instructions, message = build_reevaluate_prompt(goal, plan_text, output[:500])
                    reeval = await self._codex_call_json(instructions, message)
                    if isinstance(reeval, list):
                        remaining = reeval
                        self._rewrite_remaining_subtasks(plan_path, completed_count, remaining)
            else:
                await state.update_execution(exec_id, status="failed", output=output)
                self._bus.emit(Event(
                    event_type=EventType.CEO_SUBTASK_FAIL,
                    data={"subtask": subtask_desc, "employee_id": employee_id, "output": output[:500]},
                ))
                self._bus.emit(Event(
                    event_type=EventType.CEO_ESCALATION,
                    data={"goal_id": goal_id, "subtask": subtask_desc, "output": output[:500]},
                ))
                subtask_results.append(SubtaskResult(
                    subtask=subtask_desc, employee_id=employee_id,
                    status="escalated", output=output, attempt=attempt,
                    duration_seconds=duration,
                ))
                await state.update_goal(goal_id, status="escalated")
                self._update_plan_status(plan_path, "escalated")
                logger.error("ceo_escalation", goal_id=goal_id, subtask=subtask_desc[:80])
                return GoalResult(
                    goal_id=goal_id, status="escalated",
                    subtask_results=subtask_results, plan_path=str(plan_path),
                )

        # All subtasks complete
        await state.update_goal(goal_id, status="completed")
        self._update_plan_status(plan_path, "completed")
        self._bus.emit(Event(event_type=EventType.CEO_GOAL_COMPLETE, data={"goal_id": goal_id}))
        logger.info("ceo_goal_complete", goal_id=goal_id)

        return GoalResult(
            goal_id=goal_id, status="completed",
            subtask_results=subtask_results, plan_path=str(plan_path),
        )

    async def dispatch(self, task_id: str | None = None) -> TaskResult:
        """Execute a standalone task from the queue."""
        state = self._require_state()
        self._check_roster()

        if task_id:
            task = await state.get_task(task_id)
        else:
            pending = await state.list_pending_tasks()
            if not pending:
                msg = "No pending tasks in queue"
                raise RuntimeError(msg)
            task = pending[0]
            task_id = task["id"]

        if not task:
            msg = f"Task {task_id} not found"
            raise RuntimeError(msg)

        await state.update_task(task_id, status="in_progress")

        # Assign
        roster = self._roster_summary()
        instructions, message = build_assign_prompt(
            subtask=task["description"],
            goal_context=task["description"],
            roster_details=roster,
            previous_results=[],
        )
        assign_result = await self._codex_call_json(instructions, message)
        employee_id = assign_result.get("employee_id", "")
        if not self._registry.get(employee_id):
            employee_id = self._registry.list_active()[0].id

        # Dispatch
        start_time = time.monotonic()
        output, exit_code, success = await self._dispatch_employee(employee_id, task["description"])
        attempt = 1

        exec_id = await state.record_execution(
            goal_id=None, task_id=task_id, subtask=task["description"],
            employee_id=employee_id, attempt=attempt,
        )

        if not success:
            await state.update_execution(exec_id, status="failed", output=output)
            attempt = 2
            output, exit_code, success = await self._dispatch_employee(
                employee_id, task["description"], failure_context=output
            )
            exec_id = await state.record_execution(
                goal_id=None, task_id=task_id, subtask=task["description"],
                employee_id=employee_id, attempt=attempt,
            )

        duration = time.monotonic() - start_time

        if success:
            await state.update_execution(exec_id, status="completed", output=output)
            await state.update_task(task_id, status="completed", result=output[:500])
            return TaskResult(
                task_id=task_id, status="completed",
                employee_id=employee_id, output=output, duration_seconds=duration,
            )

        await state.update_execution(exec_id, status="failed", output=output)
        await state.update_task(task_id, status="escalated", result=output[:500])
        return TaskResult(
            task_id=task_id, status="escalated",
            employee_id=employee_id, output=output, duration_seconds=duration,
        )

    async def resume(self, goal_id: str) -> GoalResult:
        """Resume an escalated goal from last incomplete subtask."""
        state = self._require_state()
        self._check_roster()
        goal = await state.get_goal(goal_id)
        if not goal:
            msg = f"Goal {goal_id} not found"
            raise RuntimeError(msg)

        plan_path = Path(goal["plan_path"])
        if not plan_path.exists():
            msg = f"Plan file not found: {plan_path}"
            raise RuntimeError(msg)

        # Parse remaining subtasks from plan markdown
        remaining = self._parse_remaining_subtasks(plan_path)
        if not remaining:
            msg = "No remaining subtasks to resume"
            raise RuntimeError(msg)

        await state.update_goal(goal_id, status="executing")
        return await self._execute_plan(
            goal_id=goal_id,
            goal=goal["description"],
            plan_path=plan_path,
            remaining=remaining,
            completed_count=self._count_completed_subtasks(plan_path),
        )

    def _parse_remaining_subtasks(self, plan_path: Path) -> list[dict[str, Any]]:
        """Parse unchecked subtasks from plan markdown."""
        import re
        content = plan_path.read_text()
        remaining = []
        for match in re.finditer(r"- \[ \] \*\*\d+\.\s+(.+?)\*\*", content):
            remaining.append({"description": match.group(1).strip()})
        return remaining

    def _count_completed_subtasks(self, plan_path: Path) -> int:
        """Count checked subtasks in plan markdown."""
        import re
        content = plan_path.read_text()
        return len(re.findall(r"- \[x\] \*\*", content))

    def _count_total_subtasks(self, plan_path: Path) -> int:
        """Count all subtasks (checked + unchecked) in plan markdown."""
        import re
        content = plan_path.read_text()
        return len(re.findall(r"- \[[ x]\] \*\*", content))

    async def status(self) -> list[GoalStatus | TaskStatus]:
        """Return current state of all goals and tasks."""
        state = self._require_state()
        items = await state.list_all_status()
        result: list[GoalStatus | TaskStatus] = []
        for item in items:
            if item.get("type") == "goal":
                # Count subtasks from plan markdown
                plan_p = Path(item.get("plan_path", ""))
                total = self._count_total_subtasks(plan_p) if plan_p.exists() else 0
                completed = self._count_completed_subtasks(plan_p) if plan_p.exists() else 0
                result.append(GoalStatus(
                    goal_id=item["id"], description=item["description"],
                    status=item["status"], subtasks_completed=completed,
                    subtasks_total=total, plan_path=item.get("plan_path", ""),
                ))
            else:
                result.append(TaskStatus(
                    task_id=item["id"], description=item["description"],
                    status=item["status"], priority=item.get("priority", 0),
                ))
        return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/gray/dev/AutoGenesis && python -m pytest packages/employees/tests/test_orchestrator.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add packages/employees/src/autogenesis_employees/orchestrator.py packages/employees/tests/test_orchestrator.py
git commit -m "feat(ceo): add CEOOrchestrator — goal decomposition, assignment, dispatch, retry, escalation"
```

---

### Task 6: CLI Commands

**Files:**
- Create: `packages/cli/src/autogenesis_cli/commands/ceo.py`
- Modify: `packages/cli/src/autogenesis_cli/app.py:9,56` — import and register ceo_app

Follow the same pattern as `hr.py`: lazy imports, Typer sub-app, Rich tables.

- [ ] **Step 1: Write the CLI module**

```python
"""CEO subcommand group — orchestrate agent employees."""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

console = Console()

ceo_app = typer.Typer(name="ceo", help="CEO Orchestrator — manage goals and tasks.", no_args_is_help=True)


def _get_orchestrator():
    """Lazy-build a CEOOrchestrator with real dependencies."""
    from pathlib import Path

    from autogenesis_core.config import load_config
    from autogenesis_core.credentials import EnvCredentialProvider
    from autogenesis_core.client import CodexClient, CodexClientConfig
    from autogenesis_core.sub_agents import SubAgentManager
    from autogenesis_employees.orchestrator import CEOOrchestrator
    from autogenesis_employees.registry import EmployeeRegistry
    from autogenesis_employees.runtime import EmployeeRuntime

    cfg = load_config()

    # Registry
    import os
    xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    global_dir = Path(cfg.employees.global_roster_path) if cfg.employees.global_roster_path else Path(xdg) / "autogenesis" / "employees"
    registry = EmployeeRegistry(global_dir=global_dir)

    # Codex client
    creds = EnvCredentialProvider()
    codex = CodexClient(creds, CodexClientConfig(
        model=cfg.codex.model,
        api_base_url=cfg.codex.api_base_url,
        timeout=cfg.codex.timeout,
    ))

    return CEOOrchestrator(
        registry=registry,
        runtime=EmployeeRuntime(),
        sub_agent_mgr=SubAgentManager(),
        codex=codex,
        dispatch_timeout=cfg.employees.dispatch_timeout,
    )


def _run_async(coro):
    """Run an async coroutine from sync Typer command."""
    return asyncio.run(coro)


@ceo_app.command(name="enqueue")
def ceo_enqueue(
    description: str = typer.Argument(help="Task description"),
    priority: int = typer.Option(0, "--priority", "-p", help="Priority (higher = first)"),
) -> None:
    """Push a task onto the CEO queue."""

    async def _run():
        orch = _get_orchestrator()
        await orch.initialize()
        task_id = await orch.enqueue(description, priority=priority)
        console.print(f"[green]Enqueued:[/green] {task_id}")
        await orch.close()

    _run_async(_run())


@ceo_app.command(name="run")
def ceo_run(
    goal: str = typer.Argument(help="High-level goal to decompose and execute"),
) -> None:
    """Decompose a goal and execute via employee dispatch."""

    async def _run():
        orch = _get_orchestrator()
        await orch.initialize()
        try:
            result = await orch.run(goal)
            if result.status == "completed":
                console.print(f"\n[bold green]Goal completed![/bold green]")
            else:
                console.print(f"\n[bold red]Goal escalated — needs manual intervention.[/bold red]")

            table = Table(title="Subtask Results")
            table.add_column("Subtask")
            table.add_column("Employee")
            table.add_column("Status")
            table.add_column("Attempt")
            table.add_column("Duration")

            for sr in result.subtask_results:
                style = "green" if sr.status == "completed" else "red"
                table.add_row(
                    sr.subtask[:60], sr.employee_id, sr.status,
                    str(sr.attempt), f"{sr.duration_seconds:.1f}s",
                    style=style,
                )
            console.print(table)
            console.print(f"\nPlan: {result.plan_path}")
        except RuntimeError as e:
            console.print(f"[red]Error:[/red] {e}")
        finally:
            await orch.close()

    _run_async(_run())


@ceo_app.command(name="dispatch")
def ceo_dispatch(
    task_id: str = typer.Argument(None, help="Specific task ID (or dispatches highest priority)"),
) -> None:
    """Execute next queued task or a specific one."""

    async def _run():
        orch = _get_orchestrator()
        await orch.initialize()
        try:
            result = await orch.dispatch(task_id)
            style = "green" if result.status == "completed" else "red"
            console.print(f"[{style}]{result.status}[/{style}] — {result.employee_id} ({result.duration_seconds:.1f}s)")
            if result.output:
                console.print(result.output[:500])
        except RuntimeError as e:
            console.print(f"[red]Error:[/red] {e}")
        finally:
            await orch.close()

    _run_async(_run())


@ceo_app.command(name="status")
def ceo_status() -> None:
    """Show status of all goals and tasks."""

    async def _run():
        orch = _get_orchestrator()
        await orch.initialize()
        items = await orch.status()

        from autogenesis_employees.ceo_models import GoalStatus

        if not items:
            console.print("[dim]No goals or tasks.[/dim]")
            await orch.close()
            return

        table = Table(title="CEO Status")
        table.add_column("Type")
        table.add_column("ID", style="dim")
        table.add_column("Description")
        table.add_column("Status")
        table.add_column("Details")

        for item in items:
            if isinstance(item, GoalStatus):
                style = "green" if item.status == "completed" else "yellow"
                table.add_row(
                    "goal", item.goal_id, item.description[:50],
                    item.status, f"{item.subtasks_completed}/{item.subtasks_total}",
                    style=style,
                )
            else:
                style = "green" if item.status == "completed" else "cyan"
                table.add_row(
                    "task", item.task_id, item.description[:50],
                    item.status, f"pri={item.priority}",
                    style=style,
                )
        console.print(table)
        await orch.close()

    _run_async(_run())


@ceo_app.command(name="plan")
def ceo_plan(
    goal_id: str = typer.Argument(help="Goal ID to show plan for"),
) -> None:
    """Print the markdown plan for a goal."""

    async def _run():
        orch = _get_orchestrator()
        await orch.initialize()
        state = orch._require_state()
        goal = await state.get_goal(goal_id)
        if not goal:
            console.print(f"[red]Goal {goal_id} not found.[/red]")
            await orch.close()
            return
        from pathlib import Path
        plan_path = Path(goal["plan_path"])
        if plan_path.exists():
            console.print(plan_path.read_text())
        else:
            console.print(f"[red]Plan file not found: {plan_path}[/red]")
        await orch.close()

    _run_async(_run())


@ceo_app.command(name="resume")
def ceo_resume(
    goal_id: str = typer.Argument(help="Goal ID to resume"),
) -> None:
    """Resume an escalated or paused goal."""

    async def _run():
        orch = _get_orchestrator()
        await orch.initialize()
        try:
            result = await orch.resume(goal_id)
            style = "green" if result.status == "completed" else "red"
            console.print(f"[{style}]Goal {result.status}[/{style}]")
        except RuntimeError as e:
            console.print(f"[red]Error:[/red] {e}")
        finally:
            await orch.close()

    _run_async(_run())
```

- [ ] **Step 2: Register in app.py**

In `packages/cli/src/autogenesis_cli/app.py`, add the import:
```python
from autogenesis_cli.commands.ceo import ceo_app
```

And add the registration after the existing `app.add_typer` lines:
```python
app.add_typer(ceo_app, name="ceo")
```

- [ ] **Step 3: Verify CLI loads**

Run: `cd /home/gray/dev/AutoGenesis && python -m autogenesis_cli.app --help`
Expected: Output includes `ceo` in the commands list

- [ ] **Step 4: Commit**

```bash
git add packages/cli/src/autogenesis_cli/commands/ceo.py packages/cli/src/autogenesis_cli/app.py
git commit -m "feat(ceo): add CLI commands — enqueue, run, dispatch, status, plan, resume"
```

---

### Task 7: Run Full Test Suite

**Files:** None (verification only)

- [ ] **Step 1: Run all employees package tests**

Run: `cd /home/gray/dev/AutoGenesis && python -m pytest packages/employees/tests/ -v`
Expected: All tests PASS (existing + new)

- [ ] **Step 2: Run all core package tests**

Run: `cd /home/gray/dev/AutoGenesis && python -m pytest packages/core/tests/ -v`
Expected: All tests PASS (including updated event count)

- [ ] **Step 3: Run full workspace tests**

Run: `cd /home/gray/dev/AutoGenesis && python -m pytest --tb=short`
Expected: All tests PASS across all packages

- [ ] **Step 4: Final commit if any ruff fixes needed**

Run: `cd /home/gray/dev/AutoGenesis && ruff check packages/employees/src/autogenesis_employees/ packages/cli/src/autogenesis_cli/commands/ceo.py --fix`
Fix any issues, then:
```bash
git add -u
git commit -m "fix: ruff lint fixes for CEO orchestrator"
```
