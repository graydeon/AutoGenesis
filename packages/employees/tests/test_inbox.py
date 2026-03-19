"""Tests for InboxManager — async message queue."""

from __future__ import annotations

from autogenesis_employees.inbox import InboxManager
from autogenesis_employees.models import InboxMessage


class TestInboxManager:
    async def test_send_and_receive(self, tmp_path):
        mgr = InboxManager(db_path=tmp_path / "inbox.db")
        await mgr.initialize()
        msg = InboxMessage(
            from_employee="cto", to_employee="be", subject="Review", body="Please review auth"
        )
        await mgr.send(msg)
        unread = await mgr.get_unread("be")
        assert len(unread) == 1
        assert unread[0].subject == "Review"
        await mgr.close()

    async def test_mark_read(self, tmp_path):
        mgr = InboxManager(db_path=tmp_path / "inbox.db")
        await mgr.initialize()
        msg = InboxMessage(from_employee="cto", to_employee="be", subject="Hi", body="Hello")
        await mgr.send(msg)
        await mgr.mark_read(msg.id)
        unread = await mgr.get_unread("be")
        assert len(unread) == 0
        await mgr.close()

    async def test_multiple_recipients(self, tmp_path):
        mgr = InboxManager(db_path=tmp_path / "inbox.db")
        await mgr.initialize()
        await mgr.send(InboxMessage(from_employee="cto", to_employee="be", subject="1", body="one"))
        await mgr.send(InboxMessage(from_employee="cto", to_employee="fe", subject="2", body="two"))
        assert len(await mgr.get_unread("be")) == 1
        assert len(await mgr.get_unread("fe")) == 1
        assert len(await mgr.get_unread("cto")) == 0
        await mgr.close()
