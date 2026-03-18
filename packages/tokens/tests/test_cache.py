"""Tests for response cache."""

from __future__ import annotations

import time
from unittest.mock import patch

from autogenesis_tokens.cache import ResponseCache


class TestResponseCache:
    def test_store_and_retrieve(self, tmp_path):
        cache = ResponseCache(db_path=tmp_path / "cache.db")
        messages = [{"role": "user", "content": "Hello"}]

        cache.put(messages, "Hi there!", model="gpt-4o")
        result = cache.get(messages)

        assert result == "Hi there!"
        cache.close()

    def test_cache_miss(self, tmp_path):
        cache = ResponseCache(db_path=tmp_path / "cache.db")
        result = cache.get([{"role": "user", "content": "Unknown"}])
        assert result is None
        cache.close()

    def test_ttl_expiration(self, tmp_path):
        cache = ResponseCache(db_path=tmp_path / "cache.db", ttl_seconds=1)
        messages = [{"role": "user", "content": "Hello"}]
        cache.put(messages, "Hi!")

        # Mock time to be past TTL
        with patch("autogenesis_tokens.cache.time") as mock_time:
            mock_time.time.return_value = time.time() + 2
            result = cache.get(messages)

        assert result is None
        cache.close()

    def test_invalidate_all(self, tmp_path):
        cache = ResponseCache(db_path=tmp_path / "cache.db")
        cache.put([{"role": "user", "content": "A"}], "Response A")
        cache.put([{"role": "user", "content": "B"}], "Response B")

        removed = cache.invalidate_all()
        assert removed == 2
        assert cache.get([{"role": "user", "content": "A"}]) is None
        cache.close()

    def test_hit_and_miss_tracking(self, tmp_path):
        cache = ResponseCache(db_path=tmp_path / "cache.db")
        messages = [{"role": "user", "content": "Hello"}]
        cache.put(messages, "Hi!")

        cache.get(messages)  # hit
        cache.get([{"role": "user", "content": "other"}])  # miss

        assert cache.hits == 1
        assert cache.misses == 1
        cache.close()
