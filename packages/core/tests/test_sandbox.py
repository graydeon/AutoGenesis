"""Tests for sandbox provider ABC."""

from __future__ import annotations

import pytest
from autogenesis_core.sandbox import SandboxProvider


class TestSandboxProvider:
    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            SandboxProvider()

    def test_concrete_subclass_works(self):
        class MockSandbox(SandboxProvider):
            async def execute(
                self,
                command: str,
                timeout: float = 30.0,
                cwd: str | None = None,
            ) -> tuple[str, int]:
                return ("output", 0)

            async def cleanup(self) -> None:
                pass

        sandbox = MockSandbox()
        assert sandbox is not None
