"""Tests for SQLite-backed queue manager."""

from __future__ import annotations

from autogenesis_twitter.models import QueueItem, TweetData
from autogenesis_twitter.queue import QueueManager


class TestQueueManager:
    async def test_add_and_list_pending(self, tmp_path):
        mgr = QueueManager(db_path=tmp_path / "queue.db")
        await mgr.initialize()
        item = QueueItem(type="original", draft_text="hello world")
        await mgr.add(item)
        pending = await mgr.list_pending()
        assert len(pending) == 1
        assert pending[0].draft_text == "hello world"
        await mgr.close()

    async def test_approve(self, tmp_path):
        mgr = QueueManager(db_path=tmp_path / "queue.db")
        await mgr.initialize()
        item = QueueItem(type="original", draft_text="test")
        await mgr.add(item)
        await mgr.approve(item.id)
        pending = await mgr.list_pending()
        assert len(pending) == 0
        approved = await mgr.list_approved()
        assert len(approved) == 1
        await mgr.close()

    async def test_reject_with_reason(self, tmp_path):
        mgr = QueueManager(db_path=tmp_path / "queue.db")
        await mgr.initialize()
        item = QueueItem(type="original", draft_text="test")
        await mgr.add(item)
        await mgr.reject(item.id, reason="too aggressive")
        rejected = await mgr.list_by_status("rejected")
        assert len(rejected) == 1
        assert rejected[0].rejection_reason == "too aggressive"
        await mgr.close()

    async def test_mark_posted(self, tmp_path):
        mgr = QueueManager(db_path=tmp_path / "queue.db")
        await mgr.initialize()
        item = QueueItem(type="original", draft_text="test")
        await mgr.add(item)
        await mgr.approve(item.id)
        await mgr.mark_posted(item.id)
        posted = await mgr.list_by_status("posted")
        assert len(posted) == 1
        await mgr.close()

    async def test_mark_failed(self, tmp_path):
        mgr = QueueManager(db_path=tmp_path / "queue.db")
        await mgr.initialize()
        item = QueueItem(type="original", draft_text="test")
        await mgr.add(item)
        await mgr.approve(item.id)
        await mgr.mark_failed(item.id, reason="rate limited")
        failed = await mgr.list_by_status("failed")
        assert len(failed) == 1
        assert failed[0].failure_reason == "rate limited"
        await mgr.close()

    async def test_reply_with_context(self, tmp_path):
        mgr = QueueManager(db_path=tmp_path / "queue.db")
        await mgr.initialize()
        tweet = TweetData(id="99", author="@bob", text="what do you think?", timestamp="1h")
        item = QueueItem(type="reply", draft_text="great point", in_reply_to=tweet)
        await mgr.add(item)
        pending = await mgr.list_pending()
        assert pending[0].in_reply_to is not None
        assert pending[0].in_reply_to.author == "@bob"
        await mgr.close()

    async def test_update_draft_text(self, tmp_path):
        mgr = QueueManager(db_path=tmp_path / "queue.db")
        await mgr.initialize()
        item = QueueItem(type="original", draft_text="old text")
        await mgr.add(item)
        await mgr.update_draft(item.id, "new text")
        pending = await mgr.list_pending()
        assert pending[0].draft_text == "new text"
        await mgr.close()
