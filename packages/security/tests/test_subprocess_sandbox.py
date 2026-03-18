"""Tests for subprocess sandbox."""

from __future__ import annotations

from autogenesis_security.sandbox import SubprocessSandbox


class TestSubprocessSandbox:
    async def test_execute_simple_command(self):
        sandbox = SubprocessSandbox()
        output, code = await sandbox.execute("echo hello")
        assert code == 0
        assert "hello" in output

    async def test_timeout_kills_process(self):
        sandbox = SubprocessSandbox()
        _output, code = await sandbox.execute("sleep 60", timeout=0.5)
        assert code != 0

    async def test_failed_command(self):
        sandbox = SubprocessSandbox()
        _output, code = await sandbox.execute("false")
        assert code != 0

    async def test_cleanup(self):
        sandbox = SubprocessSandbox()
        await sandbox.cleanup()  # should not raise
