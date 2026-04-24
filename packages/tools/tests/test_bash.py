"""Tests for BashTool."""

from __future__ import annotations

from autogenesis_core.models import ToolCall
from autogenesis_tools.bash import BashTool


class TestBashTool:
    async def test_basic_command(self):
        tool = BashTool()
        tc = ToolCall(name="bash", arguments={"command": "echo hello"})
        result = await tool(tc)
        assert "hello" in result

    async def test_returns_exit_code_on_failure(self):
        tool = BashTool()
        tc = ToolCall(
            name="bash",
            arguments={"command": "python3 -c 'import sys; sys.exit(42)'"},
        )
        result = await tool(tc)
        assert "Exit code 42" in result

    async def test_timeout_kills_process(self):
        tool = BashTool()
        tc = ToolCall(name="bash", arguments={"command": "sleep 60", "timeout": 0.5})
        result = await tool(tc)
        assert "timed out" in result.lower()

    async def test_ansi_stripping(self):
        tool = BashTool()
        tc = ToolCall(name="bash", arguments={"command": "echo -e '\\033[31mred\\033[0m'"})
        result = await tool(tc)
        assert "\x1b[" not in result
        assert "red" in result

    async def test_output_truncation(self):
        tool = BashTool()
        # Generate output larger than 2000 chars
        tc = ToolCall(name="bash", arguments={"command": "python3 -c \"print('x' * 5000)\""})
        result = await tool(tc)
        assert "truncated" in result.lower()

    async def test_denies_unapproved_command(self):
        tool = BashTool()
        tc = ToolCall(name="bash", arguments={"command": "sh -c 'echo unsafe'"})
        result = await tool(tc)
        assert "security policy" in result.lower()

    async def test_runs_inside_workspace_root(self, tmp_path):
        tool = BashTool(workspace_root=tmp_path)
        tc = ToolCall(name="bash", arguments={"command": "pwd"})
        result = await tool(tc)
        assert str(tmp_path) in result

    async def test_tool_definition(self):
        tool = BashTool()
        defn = tool.to_definition()
        assert defn.name == "bash"
