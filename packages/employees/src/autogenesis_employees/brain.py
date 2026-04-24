"""BrainManager — per-employee SQLite+FTS5 persistent memory.

Each employee gets their own brain.db with full-text search for recall.
Memories decay in relevance over time; accessed memories get boosted.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import aiosqlite
import structlog

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

from autogenesis_employees.models import Memory

logger = structlog.get_logger()

_CREATE_MEMORIES = """
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    project TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_accessed_at TEXT,
    relevance_score REAL DEFAULT 1.0
)
"""

_CREATE_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(content, source, category)
"""


class BrainManager:
    """Async SQLite brain for an employee."""

    def __init__(self, db_path: Path, max_memories: int = 1000) -> None:
        self._db_path = db_path
        self._max = max_memories
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Create database and tables."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self._db_path)
        await self._db.execute(_CREATE_MEMORIES)
        await self._db.execute(_CREATE_FTS)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    def _require_db(self) -> aiosqlite.Connection:
        if self._db is None:
            msg = "BrainManager not initialized — call initialize() first"
            raise RuntimeError(msg)
        return self._db

    async def write(self, memory: Memory) -> None:
        """Store a memory."""
        db = self._require_db()
        await db.execute(
            "INSERT OR REPLACE INTO memories "
            "(id, category, content, source, project, created_at, relevance_score) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                memory.id,
                memory.category,
                memory.content,
                memory.source,
                memory.project,
                memory.created_at.isoformat(),
                memory.relevance_score,
            ),
        )
        # Insert into FTS index (standalone table, not content-table)
        await db.execute(
            "INSERT INTO memories_fts (rowid, content, source, category) VALUES ("
            "(SELECT rowid FROM memories WHERE id = ?), ?, ?, ?)",
            (memory.id, memory.content, memory.source, memory.category),
        )
        await db.commit()

    async def recall(self, query: str, limit: int = 5) -> list[Memory]:
        """Search memories using FTS5. Boosts relevance of accessed memories."""
        db = self._require_db()
        try:
            cursor = await db.execute(
                "SELECT m.id, m.category, m.content, m.source, m.project, "
                "m.created_at, m.last_accessed_at, m.relevance_score "
                "FROM memories m "
                "JOIN memories_fts fts ON m.rowid = fts.rowid "
                "WHERE memories_fts MATCH ? "
                "ORDER BY m.relevance_score DESC LIMIT ?",
                (query, limit),
            )
        except aiosqlite.OperationalError:
            return []
        rows = await cursor.fetchall()
        memories = [self._row_to_memory(row) for row in rows]

        # Boost relevance of accessed memories (reset to 1.0)
        now = datetime.now(UTC).isoformat()
        for mem in memories:
            await db.execute(
                "UPDATE memories SET relevance_score = 1.0, last_accessed_at = ? WHERE id = ?",
                (now, mem.id),
            )
        await db.commit()

        return memories

    async def decay_all(self, factor: float = 0.95) -> None:
        """Apply relevance decay to all memories. Call daily."""
        db = self._require_db()
        await db.execute("UPDATE memories SET relevance_score = relevance_score * ?", (factor,))
        await db.commit()

    async def top_memories(self, limit: int = 20) -> list[Memory]:
        """Get top N memories by relevance score."""
        db = self._require_db()
        cursor = await db.execute(
            "SELECT id, category, content, source, project, "
            "created_at, last_accessed_at, relevance_score "
            "FROM memories ORDER BY relevance_score DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_memory(row) for row in rows]

    async def count(self) -> int:
        """Count total memories."""
        db = self._require_db()
        cursor = await db.execute("SELECT COUNT(*) FROM memories")
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def prune(self) -> int:
        """Remove lowest-relevance memories if over limit."""
        db = self._require_db()
        total = await self.count()
        if total <= self._max:
            return 0
        to_remove = total - self._max
        # Delete from FTS first
        await db.execute(
            "DELETE FROM memories_fts WHERE rowid IN ("
            "SELECT rowid FROM memories ORDER BY relevance_score ASC LIMIT ?)",
            (to_remove,),
        )
        await db.execute(
            "DELETE FROM memories WHERE id IN ("
            "SELECT id FROM memories ORDER BY relevance_score ASC LIMIT ?)",
            (to_remove,),
        )
        await db.commit()
        logger.info("brain_pruned", removed=to_remove)
        return to_remove

    def _row_to_memory(self, row: Sequence[Any]) -> Memory:
        return Memory(
            id=row[0],
            category=row[1],
            content=row[2],
            source=row[3],
            project=row[4],
            created_at=datetime.fromisoformat(row[5]),
            last_accessed_at=datetime.fromisoformat(row[6]) if row[6] else None,
            relevance_score=row[7],
        )
