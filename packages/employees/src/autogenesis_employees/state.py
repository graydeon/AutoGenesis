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
            await db.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", params)  # noqa: S608
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

    async def update_goal(self, goal_id: str, status: str | None = None) -> None:
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
            await db.execute(f"UPDATE goals SET {', '.join(updates)} WHERE id = ?", params)  # noqa: S608
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
            "INSERT INTO executions"
            " (id, goal_id, task_id, subtask, employee_id, attempt, started_at)"
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
            await db.execute(f"UPDATE executions SET {', '.join(updates)} WHERE id = ?", params)  # noqa: S608
            await db.commit()

    async def list_executions(
        self, goal_id: str | None = None, task_id: str | None = None
    ) -> list[dict[str, Any]]:
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
        cursor = await db.execute("SELECT * FROM goals ORDER BY created_at DESC")
        items: list[dict[str, Any]] = [
            {**dict(row), "type": "goal"} for row in await cursor.fetchall()
        ]
        cursor = await db.execute("SELECT * FROM tasks ORDER BY priority DESC, created_at DESC")
        items.extend({**dict(row), "type": "task"} for row in await cursor.fetchall())
        return items
