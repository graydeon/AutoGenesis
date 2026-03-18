"""Concrete sandbox implementations."""

from __future__ import annotations

import asyncio

from autogenesis_core.sandbox import SandboxProvider


class SubprocessSandbox(SandboxProvider):
    """Sandbox using asyncio subprocess with timeout."""

    async def execute(
        self,
        command: str,
        timeout: float = 30.0,  # noqa: ASYNC109
        cwd: str | None = None,
    ) -> tuple[str, int]:
        """Execute command in subprocess with timeout."""
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=cwd,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            if proc is not None:
                proc.kill()
            return (f"Timed out after {timeout}s", -1)

        output = stdout.decode(errors="replace") if stdout else ""
        return (output, proc.returncode or 0)

    async def cleanup(self) -> None:
        """No persistent resources to clean up."""
