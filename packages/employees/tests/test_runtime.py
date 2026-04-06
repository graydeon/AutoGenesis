"""Tests for EmployeeRuntime — context building."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from autogenesis_employees.models import EmployeeConfig
from autogenesis_employees.runtime import EmployeeRuntime


class TestEmployeeRuntime:
    def test_build_system_prompt(self):
        config = EmployeeConfig(
            id="be",
            title="Backend Engineer",
            persona="You are a backend engineer.",
            training_directives=["Always use async/await"],
        )
        runtime = EmployeeRuntime()
        prompt = runtime.build_system_prompt(
            config=config,
            brain_context=["Remember: use pytest fixtures"],
            inbox_messages=["From CTO: Review the auth module"],
            changelog_entries=["## 2026-03-19 — cto\n**Task:** Init project"],
            project_context="## GitNexus Code Context\n\nAuth flow: router -> service -> repo",
            task="Build the user API",
        )
        assert "backend engineer" in prompt.lower()
        assert "async/await" in prompt
        assert "pytest fixtures" in prompt
        assert "Review the auth module" in prompt
        assert "GitNexus Code Context" in prompt
        assert "Build the user API" in prompt

    def test_build_tool_whitelist(self):
        config = EmployeeConfig(
            id="be",
            title="BE",
            persona="p",
            tools=["bash", "file_read", "nonexistent"],
        )
        runtime = EmployeeRuntime()
        available = ["bash", "file_read", "file_write", "grep"]
        filtered = runtime.filter_tools(config.tools, available)
        assert "bash" in filtered
        assert "file_read" in filtered
        assert "nonexistent" not in filtered
        assert "file_write" not in filtered

    async def test_dispatch_calls_spawn(self):
        config = EmployeeConfig(id="test", title="Test", persona="testing")
        mgr = MagicMock()
        mock_result = MagicMock()
        mgr.spawn = AsyncMock(return_value=mock_result)
        runtime = EmployeeRuntime()
        result = await runtime.dispatch(config, "do stuff", mgr)
        assert result is mock_result
        mgr.spawn.assert_called_once()
        # Verify system_prompt was passed
        call_kwargs = mgr.spawn.call_args
        assert "system_prompt" in call_kwargs.kwargs or len(call_kwargs.args) >= 4
