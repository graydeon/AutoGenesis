"""Tests for SubAgentManager — supervised Codex CLI subprocess orchestration."""

from __future__ import annotations

import asyncio

import pytest
from autogenesis_core.sub_agents import SubAgentManager, SubAgentResult


class TestSubAgentResult:
    def test_success(self):
        r = SubAgentResult(output="done", exit_code=0)
        assert r.success is True

    def test_failure(self):
        r = SubAgentResult(output="error", exit_code=1)
        assert r.success is False


class TestSubAgentManager:
    async def test_spawn_returns_result(self):
        """Spawn a simple echo command as sub-agent."""
        mgr = SubAgentManager(codex_binary="echo")
        result = await mgr.spawn(task="hello world", cwd="/tmp")
        assert result.exit_code == 0
        assert "hello" in result.output.lower() or result.output != ""

    async def test_concurrency_limit(self):
        mgr = SubAgentManager(max_concurrent=1, codex_binary="sleep")
        assert mgr.max_concurrent == 1

    async def test_cancel(self):
        mgr = SubAgentManager(codex_binary="sleep")
        task = asyncio.create_task(mgr.spawn(task="10", cwd="/tmp"))
        await asyncio.sleep(0.1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    async def test_timeout(self):
        mgr = SubAgentManager(codex_binary="sleep")
        result = await mgr.spawn(task="10", cwd="/tmp", timeout=0.5)
        assert result.exit_code != 0 or result.timed_out is True

    async def test_depth_env_var(self):
        """AUTOGENESIS_AGENT_DEPTH is set for child processes."""
        mgr = SubAgentManager(codex_binary="env")
        result = await mgr.spawn(task="", cwd="/tmp")
        assert "AUTOGENESIS_AGENT_DEPTH=1" in result.output


class TestSubAgentManagerExtended:
    async def test_spawn_with_env_overrides(self):
        mgr = SubAgentManager(codex_binary="env")
        result = await mgr.spawn(task="", cwd="/tmp", env_overrides={"CUSTOM_VAR": "hello"})
        assert "CUSTOM_VAR=hello" in result.output
