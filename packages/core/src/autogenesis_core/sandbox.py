"""Sandbox provider abstract interface. Concrete implementations in security package."""

from __future__ import annotations

from abc import ABC, abstractmethod


class SandboxProvider(ABC):
    """Abstract base for execution sandboxing."""

    @abstractmethod
    async def execute(
        self,
        command: str,
        timeout: float = 30.0,  # noqa: ASYNC109
        cwd: str | None = None,
    ) -> tuple[str, int]:
        """Execute command in sandbox. Returns (output, exit_code)."""

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up sandbox resources."""
