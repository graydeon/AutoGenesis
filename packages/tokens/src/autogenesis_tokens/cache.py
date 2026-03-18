"""Exact-match response caching with SQLite backend."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from os import environ
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()

_DEFAULT_TTL_SECONDS = 3600  # 1 hour


def _default_cache_path() -> Path:
    xdg_cache = environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))
    return Path(xdg_cache) / "autogenesis" / "cache.db"


def _hash_messages(messages: list[dict[str, Any]]) -> str:
    """Create deterministic hash of messages."""
    content = json.dumps(messages, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


class ResponseCache:
    """Exact-match response cache backed by SQLite."""

    def __init__(
        self,
        db_path: Path | None = None,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
    ) -> None:
        self._ttl = ttl_seconds
        path = db_path or _default_cache_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path))
        self._init_db()
        self._hits = 0
        self._misses = 0

    def _init_db(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                response TEXT NOT NULL,
                model TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        self._conn.commit()

    def get(self, messages: list[dict[str, Any]]) -> str | None:
        """Look up cached response. Returns None on miss or expiry."""
        key = _hash_messages(messages)
        row = self._conn.execute(
            "SELECT response, created_at FROM cache WHERE key = ?", (key,)
        ).fetchone()

        if row is None:
            self._misses += 1
            return None

        response, created_at = row
        if time.time() - created_at > self._ttl:
            self._conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            self._conn.commit()
            self._misses += 1
            return None

        self._hits += 1
        return response  # type: ignore[no-any-return]

    def put(
        self,
        messages: list[dict[str, Any]],
        response: str,
        model: str = "",
    ) -> None:
        """Store a response in cache."""
        key = _hash_messages(messages)
        self._conn.execute(
            "INSERT OR REPLACE INTO cache (key, response, model, created_at) VALUES (?, ?, ?, ?)",
            (key, response, model, time.time()),
        )
        self._conn.commit()

    def invalidate_all(self) -> int:
        """Clear all cache entries. Returns count deleted."""
        cursor = self._conn.execute("DELETE FROM cache")
        self._conn.commit()
        return cursor.rowcount

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
