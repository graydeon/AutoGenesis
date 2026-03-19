"""Tests for Twitter data models."""

from __future__ import annotations

import pytest
from autogenesis_twitter.models import (
    QueueItem,
    SessionState,
    TweetData,
    TweetMetrics,
    WorldviewState,
)


class TestTweetMetrics:
    def test_defaults(self):
        m = TweetMetrics()
        assert m.likes == 0
        assert m.retweets == 0
        assert m.replies == 0


class TestTweetData:
    def test_basic(self):
        t = TweetData(id="123", author="@user", text="hello", timestamp="2026-03-18T10:00:00Z")
        assert t.id == "123"
        assert t.is_reply_to is None

    def test_text_truncation(self):
        long_text = "x" * 600
        t = TweetData(id="1", author="@a", text=long_text, timestamp="now")
        assert len(t.text) <= 500

    def test_serialization_roundtrip(self):
        t = TweetData(id="1", author="@a", text="hi", timestamp="now")
        data = t.model_dump()
        restored = TweetData.model_validate(data)
        assert restored.id == "1"


class TestQueueItem:
    def test_pending_by_default(self):
        q = QueueItem(type="original", draft_text="hello world")
        assert q.status == "pending"
        assert q.id != ""
        assert q.in_reply_to is None

    def test_reply_with_context(self):
        tweet = TweetData(id="99", author="@bob", text="thoughts?", timestamp="now")
        q = QueueItem(type="reply", draft_text="great take", in_reply_to=tweet)
        assert q.in_reply_to.author == "@bob"

    def test_valid_types(self):
        QueueItem(type="original", draft_text="hi")
        QueueItem(type="reply", draft_text="hi")
        with pytest.raises(Exception):
            QueueItem(type="retweet", draft_text="hi")


class TestWorldviewState:
    def test_defaults(self):
        w = WorldviewState()
        assert w.topics_of_interest == []
        assert w.people_i_engage_with == []
        assert w.opinions_formed == []

    def test_serialization(self):
        w = WorldviewState(topics_of_interest=["AI safety", "open source"])
        data = w.model_dump_json()
        restored = WorldviewState.model_validate_json(data)
        assert "AI safety" in restored.topics_of_interest


class TestSessionState:
    def test_defaults(self):
        s = SessionState()
        assert s.active is False
        assert s.permission_granted is False
