"""SQLite-backed draft queue manager.

Atomic reads/writes for concurrent access from agent, dashboard, and CLI.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import aiosqlite

from autogenesis_twitter.models import QueueItem, TweetData

if TYPE_CHECKING:
    from pathlib import Path

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS queue (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    draft_text TEXT NOT NULL,
    in_reply_to_json TEXT,
    created_at TEXT NOT NULL,
    reviewed_at TEXT,
    posted_at TEXT,
    rejection_reason TEXT,
    failure_reason TEXT
)
"""


class QueueManager:
    """Async SQLite queue for tweet drafts."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Create database and table if needed."""
        self._db = await aiosqlite.connect(self._db_path)
        await self._db.execute(_CREATE_TABLE)
        await self._db.commit()

    async def close(self) -> None:
        """Close database connection."""
        if self._db:
            await self._db.close()

    def _require_db(self) -> aiosqlite.Connection:
        """Return the open DB connection or raise."""
        if self._db is None:
            msg = "QueueManager not initialized; call await initialize() first"
            raise RuntimeError(msg)
        return self._db

    async def add(self, item: QueueItem) -> None:
        """Add a draft to the queue."""
        db = self._require_db()
        reply_json = item.in_reply_to.model_dump_json() if item.in_reply_to else None
        _sql = (
            "INSERT INTO queue"
            " (id, type, status, draft_text, in_reply_to_json, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)"
        )
        await db.execute(
            _sql,
            (
                item.id,
                item.type,
                item.status,
                item.draft_text,
                reply_json,
                item.created_at.isoformat(),
            ),
        )
        await db.commit()

    async def list_pending(self) -> list[QueueItem]:
        """List all pending items."""
        return await self.list_by_status("pending")

    async def list_approved(self) -> list[QueueItem]:
        """List all approved items."""
        return await self.list_by_status("approved")

    async def list_by_status(self, status: str) -> list[QueueItem]:
        """List items by status."""
        db = self._require_db()
        cursor = await db.execute(
            "SELECT * FROM queue WHERE status = ? ORDER BY created_at DESC",
            (status,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_item(row) for row in rows]

    async def approve(self, item_id: str) -> None:
        """Mark an item as approved."""
        db = self._require_db()
        now = datetime.now(UTC).isoformat()
        await db.execute(
            "UPDATE queue SET status = 'approved', reviewed_at = ? WHERE id = ?",
            (now, item_id),
        )
        await db.commit()

    async def reject(self, item_id: str, reason: str = "") -> None:
        """Mark an item as rejected."""
        db = self._require_db()
        now = datetime.now(UTC).isoformat()
        _sql = (
            "UPDATE queue SET status = 'rejected',"
            " reviewed_at = ?, rejection_reason = ? WHERE id = ?"
        )
        await db.execute(_sql, (now, reason, item_id))
        await db.commit()

    async def mark_posted(self, item_id: str) -> None:
        """Mark an item as posted."""
        db = self._require_db()
        now = datetime.now(UTC).isoformat()
        await db.execute(
            "UPDATE queue SET status = 'posted', posted_at = ? WHERE id = ?",
            (now, item_id),
        )
        await db.commit()

    async def mark_failed(self, item_id: str, reason: str = "") -> None:
        """Mark an item as failed."""
        db = self._require_db()
        await db.execute(
            "UPDATE queue SET status = 'failed', failure_reason = ? WHERE id = ?",
            (reason, item_id),
        )
        await db.commit()

    async def update_draft(self, item_id: str, new_text: str) -> None:
        """Update draft text (for edit & approve flow)."""
        db = self._require_db()
        await db.execute(
            "UPDATE queue SET draft_text = ? WHERE id = ?",
            (new_text, item_id),
        )
        await db.commit()

    def _row_to_item(self, row: tuple) -> QueueItem:
        """Convert a database row to a QueueItem."""
        reply_json = row[4]
        in_reply_to = TweetData.model_validate_json(reply_json) if reply_json else None
        return QueueItem(
            id=row[0],
            type=row[1],
            status=row[2],
            draft_text=row[3],
            in_reply_to=in_reply_to,
            created_at=datetime.fromisoformat(row[5]),
            reviewed_at=datetime.fromisoformat(row[6]) if row[6] else None,
            posted_at=datetime.fromisoformat(row[7]) if row[7] else None,
            rejection_reason=row[8],
            failure_reason=row[9],
        )
