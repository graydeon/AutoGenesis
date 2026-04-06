"""Tests for GitNexus context provider."""

from __future__ import annotations

from typing import TYPE_CHECKING

from autogenesis_employees.gitnexus import GitNexusContextProvider

if TYPE_CHECKING:
    from pathlib import Path


class TestGitNexusContextProvider:
    async def test_disabled_returns_none(self, tmp_path: Path):
        provider = GitNexusContextProvider(enabled=False)
        assert await provider.get_task_context("build auth flow", tmp_path) is None

    async def test_auto_index_then_query(self, tmp_path: Path):
        provider = GitNexusContextProvider(enabled=True, auto_index=True)
        provider._check_binary = lambda: True  # type: ignore[method-assign]

        calls: list[list[str]] = []

        async def fake_run(args: list[str], cwd: Path, deadline_seconds: float) -> tuple[int, str]:
            calls.append(args)
            if args[1] == "status":
                return 0, "Repository not indexed.\nRun: gitnexus analyze\n"
            if args[1] == "analyze":
                return 0, "Indexed successfully"
            if args[1] == "query":
                return 0, "process: auth request -> auth service -> users repo"
            return 1, "unexpected"

        provider._run = fake_run  # type: ignore[method-assign]

        context = await provider.get_task_context("auth request flow", tmp_path)
        assert context is not None
        assert "GitNexus Code Context" in context
        assert "auth service" in context
        assert [c[1] for c in calls] == ["status", "analyze", "query"]
