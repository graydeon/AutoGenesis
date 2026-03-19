"""SubAgentManager — supervised Codex CLI subprocess orchestration.

Spawns `codex` CLI as async subprocesses for delegated parallel work.
Each sub-agent is monitored and can be cancelled. Depth is enforced
via AUTOGENESIS_AGENT_DEPTH environment variable.
"""

from __future__ import annotations

import asyncio
import os

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

    async def spawn(
        self,
        task: str,
        cwd: str,
        timeout: float = 300.0,  # noqa: ASYNC109
    ) -> SubAgentResult:
        """Spawn a Codex CLI sub-agent and wait for completion."""
        depth = self._get_depth()
        env = {**os.environ, "AUTOGENESIS_AGENT_DEPTH": str(depth + 1)}

        async with self._semaphore:
            logger.info("spawning_sub_agent", task=task[:100], cwd=cwd, depth=depth + 1)

            # Only pass Codex-specific flags when using the real codex binary.
            if self._codex_binary == "codex":
                cmd_args = [self._codex_binary, "--quiet", "--full-auto", task]
            else:
                cmd_args = [self._codex_binary, task] if task else [self._codex_binary]

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

    async def cancel_all(self) -> None:
        """Terminate all active sub-agents."""
        for task_id, proc in list(self._active.items()):
            proc.terminate()
            logger.info("cancelled_sub_agent", task_id=task_id)
        self._active.clear()
