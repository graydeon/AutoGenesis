"""Concrete sandbox implementations."""

from __future__ import annotations

import asyncio
import shlex
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


class SecurityPolicyError(ValueError):
    """Raised when a sandbox policy rejects a command or path."""


@dataclass(frozen=True)
class CommandPolicy:
    """Validate subprocess commands before execution."""

    allowed_commands: frozenset[str] | None = None
    denied_commands: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "bash",
                "curl",
                "dd",
                "fish",
                "mkfs",
                "mount",
                "nc",
                "ncat",
                "rm",
                "scp",
                "sh",
                "ssh",
                "su",
                "sudo",
                "umount",
                "wget",
                "zsh",
            }
        )
    )

    def parse(self, command: str) -> list[str]:
        """Return argv for an allowed command."""
        try:
            argv = shlex.split(command)
        except ValueError as exc:
            msg = f"Invalid command syntax: {exc}"
            raise SecurityPolicyError(msg) from exc
        if not argv:
            msg = "Empty command"
            raise SecurityPolicyError(msg)

        executable = Path(argv[0]).name
        if executable in self.denied_commands:
            msg = f"Command is denied by policy: {executable}"
            raise SecurityPolicyError(msg)
        if self.allowed_commands is not None and executable not in self.allowed_commands:
            msg = f"Command is not in the allowed command set: {executable}"
            raise SecurityPolicyError(msg)
        return argv


@dataclass(frozen=True)
class WorkspacePolicy:
    """Resolve paths inside a single workspace root."""

    root: Path = field(default_factory=Path.cwd)

    @property
    def resolved_root(self) -> Path:
        return self.root.resolve(strict=False)

    def resolve_path(self, path: str | Path) -> Path:
        """Resolve a path and reject anything outside the workspace root."""
        raw_path = Path(path)
        candidate = raw_path if raw_path.is_absolute() else self.resolved_root / raw_path
        resolved = candidate.resolve(strict=False)
        if resolved != self.resolved_root and self.resolved_root not in resolved.parents:
            msg = f"Path is outside the workspace root: {path}"
            raise SecurityPolicyError(msg)
        return resolved


class SandboxProvider(ABC):
    """Abstract base for sandbox execution providers."""

    @abstractmethod
    async def execute(
        self,
        command: str,
        timeout: float = 30.0,  # noqa: ASYNC109
        cwd: str | None = None,
    ) -> tuple[str, int]:
        """Execute a command. Returns (output, exit_code)."""

    @abstractmethod
    async def cleanup(self) -> None:
        """Release any resources held by the sandbox."""


class SubprocessSandbox(SandboxProvider):
    """Sandbox using asyncio subprocess with timeout."""

    def __init__(
        self,
        *,
        workspace_root: str | Path | None = None,
        command_policy: CommandPolicy | None = None,
    ) -> None:
        self._workspace = WorkspacePolicy(Path(workspace_root) if workspace_root else Path.cwd())
        self._command_policy = command_policy or CommandPolicy()

    async def execute(
        self,
        command: str,
        timeout: float = 30.0,  # noqa: ASYNC109
        cwd: str | None = None,
    ) -> tuple[str, int]:
        """Execute command in subprocess with timeout."""
        try:
            argv = self._command_policy.parse(command)
            resolved_cwd = self._workspace.resolve_path(cwd or self._workspace.resolved_root)
        except SecurityPolicyError as exc:
            return (f"Security policy denied command: {exc}", -1)

        proc: asyncio.subprocess.Process | None = None
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=resolved_cwd,
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
