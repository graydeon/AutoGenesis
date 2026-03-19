"""SubAgentManager — supervised Codex CLI subprocess orchestration.

Spawns `codex` CLI as async subprocesses for delegated parallel work.
Each sub-agent is monitored and can be cancelled. Depth is enforced
via AUTOGENESIS_AGENT_DEPTH environment variable.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

import structlog
from pydantic import BaseModel

logger = structlog.get_logger()

_MAX_OUTPUT_CHARS = 50_000


class SubAgentResult(BaseModel):
    """Result from a sub-agent execution."""

    output: str = ""
    exit_code: int = -1
    timed_out: bool = False

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


class SubAgentManager:
    """Manages supervised Codex CLI sub-agent processes."""

    def __init__(
        self,
        max_concurrent: int = 3,
        codex_binary: str = "codex",
    ) -> None:
        self.max_concurrent = max_concurrent
        self._codex_binary = codex_binary
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active: dict[str, asyncio.subprocess.Process] = {}

    def _get_depth(self) -> int:
        return int(os.environ.get("AUTOGENESIS_AGENT_DEPTH", "0"))

    def _write_prompt_file(self, system_prompt: str) -> str | None:
        """Write system_prompt to a temp file; returns path or None if not using codex."""
        if not (system_prompt and self._codex_binary == "codex"):
            return None
        fd, prompt_path = tempfile.mkstemp(suffix=".txt", prefix="ag_prompt_")
        os.write(fd, system_prompt.encode())
        os.close(fd)
        return prompt_path

    def _cleanup_prompt_file(self, prompt_file: str | None) -> None:
        """Remove a temporary prompt file if it exists."""
        if prompt_file:
            Path(prompt_file).unlink(missing_ok=True)

    def _build_cmd_args(self, task: str, prompt_file: str | None) -> list[str]:
        """Build the command argument list."""
        if self._codex_binary == "codex":
            cmd_args = [self._codex_binary, "exec", "--full-auto"]
            if prompt_file:
                cmd_args.extend(["-c", f"model_instructions_file={prompt_file}"])
            cmd_args.append(task)
        else:
            cmd_args = [self._codex_binary, task] if task else [self._codex_binary]
        return cmd_args

    async def spawn(
        self,
        task: str,
        cwd: str,
        timeout: float = 300.0,  # noqa: ASYNC109
        system_prompt: str | None = None,
        env_overrides: dict[str, str] | None = None,
    ) -> SubAgentResult:
        """Spawn a Codex CLI sub-agent and wait for completion."""
        depth = self._get_depth()
        env = {**os.environ, "AUTOGENESIS_AGENT_DEPTH": str(depth + 1)}
        if env_overrides:
            env.update(env_overrides)

        prompt_file = self._write_prompt_file(system_prompt or "")
        cmd_args = self._build_cmd_args(task, prompt_file)

        async with self._semaphore:
            logger.info("spawning_sub_agent", task=task[:100], cwd=cwd, depth=depth + 1)

            proc = await asyncio.create_subprocess_exec(
                *cmd_args,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
            )

            task_id = f"agent_{id(proc)}"
            self._active[task_id] = proc

            try:
                stdout, _ = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout,
                )
                output = stdout.decode("utf-8", errors="replace")
                if len(output) > _MAX_OUTPUT_CHARS:
                    output = (
                        output[:_MAX_OUTPUT_CHARS] + f"\n[truncated — {len(output)} chars total]"
                    )

                return SubAgentResult(
                    output=output,
                    exit_code=proc.returncode or 0,
                )
            except TimeoutError:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5.0)
                except TimeoutError:
                    proc.kill()
                return SubAgentResult(output="Sub-agent timed out", exit_code=-1, timed_out=True)
            except asyncio.CancelledError:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5.0)
                except TimeoutError:
                    proc.kill()
                raise
            finally:
                self._active.pop(task_id, None)
                self._cleanup_prompt_file(prompt_file)

    async def cancel_all(self) -> None:
        """Terminate all active sub-agents."""
        for task_id, proc in list(self._active.items()):
            proc.terminate()
            logger.info("cancelled_sub_agent", task_id=task_id)
        self._active.clear()
