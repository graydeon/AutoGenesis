"""Tests for UnionManager — proposal ledger and voting."""

from __future__ import annotations

from autogenesis_employees.models import Proposal, Vote
from autogenesis_employees.union import UnionManager


class TestUnionManager:
    async def test_file_proposal(self, tmp_path):
        mgr = UnionManager(db_path=tmp_path / "union.db")
        await mgr.initialize()
        p = Proposal(
            title="Hire Data Engineer",
            rationale="Need SQL skills",
            category="hiring",
            filed_by="be",
        )
        await mgr.file_proposal(p)
        proposals = await mgr.list_open()
        assert len(proposals) == 1
        assert proposals[0].title == "Hire Data Engineer"
        await mgr.close()

    async def test_cast_vote(self, tmp_path):
        mgr = UnionManager(db_path=tmp_path / "union.db")
        await mgr.initialize()
        p = Proposal(title="T", rationale="R", category="tooling", filed_by="be")
        await mgr.file_proposal(p)
        v = Vote(proposal_id=p.id, employee_id="cto", vote="support", comment="Agree")
        await mgr.cast_vote(v)
        votes = await mgr.get_votes(p.id)
        assert len(votes) == 1
        assert votes[0].vote == "support"
        await mgr.close()

    async def test_resolve_proposal(self, tmp_path):
        mgr = UnionManager(db_path=tmp_path / "union.db")
        await mgr.initialize()
        p = Proposal(title="T", rationale="R", category="process", filed_by="be")
        await mgr.file_proposal(p)
        await mgr.resolve(p.id, "accepted")
        open_proposals = await mgr.list_open()
        assert len(open_proposals) == 0
        await mgr.close()
