"""UnionManager — proposal ledger and voting."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import aiosqlite
import structlog

if TYPE_CHECKING:
    from pathlib import Path

from autogenesis_employees.models import Proposal, Vote

logger = structlog.get_logger()

_CREATE_PROPOSALS = """
CREATE TABLE IF NOT EXISTS proposals (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    rationale TEXT NOT NULL,
    category TEXT NOT NULL,
    filed_by TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    resolution TEXT
)
"""

_CREATE_VOTES = """
CREATE TABLE IF NOT EXISTS votes (
    id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    vote TEXT NOT NULL,
    comment TEXT,
    created_at TEXT NOT NULL
)
"""


class UnionManager:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)  # type: ignore[union-attr]
        self._db = await aiosqlite.connect(self._db_path)
        await self._db.execute(_CREATE_PROPOSALS)
        await self._db.execute(_CREATE_VOTES)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    def _require_db(self) -> aiosqlite.Connection:
        if self._db is None:
            msg = "UnionManager not initialized"
            raise RuntimeError(msg)
        return self._db

    async def file_proposal(self, proposal: Proposal) -> None:
        db = self._require_db()
        await db.execute(
            "INSERT INTO proposals (id, title, rationale, category, filed_by, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                proposal.id,
                proposal.title,
                proposal.rationale,
                proposal.category,
                proposal.filed_by,
                proposal.status,
                proposal.created_at.isoformat(),
            ),
        )
        await db.commit()

    async def cast_vote(self, vote: Vote) -> None:
        db = self._require_db()
        await db.execute(
            "INSERT INTO votes (id, proposal_id, employee_id, vote, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                vote.id,
                vote.proposal_id,
                vote.employee_id,
                vote.vote,
                vote.comment,
                vote.created_at.isoformat(),
            ),
        )
        await db.commit()

    async def list_open(self) -> list[Proposal]:
        db = self._require_db()
        cursor = await db.execute(
            "SELECT id, title, rationale, category, filed_by, status,"
            " created_at, resolved_at, resolution"
            " FROM proposals WHERE status = 'open' ORDER BY created_at DESC",
        )
        rows = await cursor.fetchall()
        return [self._row_to_proposal(r) for r in rows]

    async def get_votes(self, proposal_id: str) -> list[Vote]:
        db = self._require_db()
        cursor = await db.execute(
            "SELECT id, proposal_id, employee_id, vote, comment, created_at "
            "FROM votes WHERE proposal_id = ? ORDER BY created_at ASC",
            (proposal_id,),
        )
        rows = await cursor.fetchall()
        return [
            Vote(
                id=r[0],
                proposal_id=r[1],
                employee_id=r[2],
                vote=r[3],
                comment=r[4],
                created_at=datetime.fromisoformat(r[5]),
            )
            for r in rows
        ]

    async def resolve(self, proposal_id: str, resolution: str) -> None:
        db = self._require_db()
        now = datetime.now(UTC).isoformat()
        await db.execute(
            "UPDATE proposals SET status = ?, resolved_at = ?, resolution = ? WHERE id = ?",
            (resolution, now, resolution, proposal_id),
        )
        await db.commit()

    def _row_to_proposal(self, row: tuple) -> Proposal:
        return Proposal(
            id=row[0],
            title=row[1],
            rationale=row[2],
            category=row[3],
            filed_by=row[4],
            status=row[5],
            created_at=datetime.fromisoformat(row[6]),
            resolved_at=datetime.fromisoformat(row[7]) if row[7] else None,
            resolution=row[8],
        )
