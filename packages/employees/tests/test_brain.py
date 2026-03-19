"""Tests for BrainManager — per-employee SQLite+FTS5 memory."""

from __future__ import annotations

from autogenesis_employees.brain import BrainManager
from autogenesis_employees.models import Memory


class TestBrainManager:
    async def test_write_and_recall(self, tmp_path):
        mgr = BrainManager(db_path=tmp_path / "brain.db")
        await mgr.initialize()
        await mgr.write(
            Memory(category="note", content="Python is great", source="self", project="test")
        )
        results = await mgr.recall("Python", limit=5)
        assert len(results) >= 1
        assert "Python" in results[0].content
        await mgr.close()

    async def test_top_memories(self, tmp_path):
        mgr = BrainManager(db_path=tmp_path / "brain.db")
        await mgr.initialize()
        for i in range(5):
            await mgr.write(
                Memory(category="note", content=f"Memory {i}", source="self", project="test")
            )
        top = await mgr.top_memories(limit=3)
        assert len(top) == 3
        await mgr.close()

    async def test_prune(self, tmp_path):
        mgr = BrainManager(db_path=tmp_path / "brain.db", max_memories=5)
        await mgr.initialize()
        for i in range(10):
            await mgr.write(
                Memory(category="note", content=f"Memory {i}", source="self", project="test")
            )
        await mgr.prune()
        count = await mgr.count()
        assert count <= 5
        await mgr.close()

    async def test_empty_recall(self, tmp_path):
        mgr = BrainManager(db_path=tmp_path / "brain.db")
        await mgr.initialize()
        results = await mgr.recall("nothing", limit=5)
        assert results == []
        await mgr.close()

    async def test_decay_all(self, tmp_path):
        mgr = BrainManager(db_path=tmp_path / "brain.db")
        await mgr.initialize()
        await mgr.write(
            Memory(category="note", content="test decay", source="self", project="test")
        )
        await mgr.decay_all(factor=0.5)
        top = await mgr.top_memories(limit=1)
        assert top[0].relevance_score < 1.0
        await mgr.close()
