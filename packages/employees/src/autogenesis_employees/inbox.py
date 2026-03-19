"""InboxManager — async inter-employee message queue."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import aiosqlite
import structlog

if TYPE_CHECKING:
    from pathlib import Path

from autogenesis_employees.models import InboxMessage

logger = structlog.get_logger()

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    from_employee TEXT NOT NULL,
    to_employee TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'unread',
    created_at TEXT NOT NULL,
    read_at TEXT
)
"""


class InboxManager:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self._db_path)
        await self._db.execute(_CREATE_TABLE)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    def _require_db(self) -> aiosqlite.Connection:
        if self._db is None:
            msg = "InboxManager not initialized"
            raise RuntimeError(msg)
        return self._db

    async def send(self, message: InboxMessage) -> None:
        db = self._require_db()
        await db.execute(
            "INSERT INTO messages"
            " (id, from_employee, to_employee, subject, body, status, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                message.id,
                message.from_employee,
                message.to_employee,
                message.subject,
                message.body,
                message.status,
                message.created_at.isoformat(),
            ),
        )
        await db.commit()
        logger.info("message_sent", from_=message.from_employee, to=message.to_employee)

    async def get_unread(self, employee_id: str) -> list[InboxMessage]:
        db = self._require_db()
        cursor = await db.execute(
            "SELECT id, from_employee, to_employee, subject, body, status, created_at, read_at "
            "FROM messages WHERE to_employee = ? AND status = 'unread' ORDER BY created_at ASC",
            (employee_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_message(row) for row in rows]

    async def mark_read(self, message_id: str) -> None:
        db = self._require_db()
        now = datetime.now(UTC).isoformat()
        await db.execute(
            "UPDATE messages SET status = 'read', read_at = ? WHERE id = ?",
            (now, message_id),
        )
        await db.commit()

    async def mark_all_read(self, employee_id: str) -> None:
        db = self._require_db()
        now = datetime.now(UTC).isoformat()
        await db.execute(
            "UPDATE messages SET status = 'read', read_at = ?"
            " WHERE to_employee = ? AND status = 'unread'",
            (now, employee_id),
        )
        await db.commit()

    def _row_to_message(self, row: tuple) -> InboxMessage:
        return InboxMessage(
            id=row[0],
            from_employee=row[1],
            to_employee=row[2],
            subject=row[3],
            body=row[4],
            status=row[5],
            created_at=datetime.fromisoformat(row[6]),
            read_at=datetime.fromisoformat(row[7]) if row[7] else None,
        )
