"""SubAgentManager — supervised Codex CLI subprocess orchestration.

Spawns `codex` CLI as async subprocesses for delegated parallel work.
Each sub-agent is monitored and can be cancelled. Depth is enforced
via AUTOGENESIS_AGENT_DEPTH environment variable.
"""

from __future__ import annotations

import asyncio
import os
import sys
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
        stream_output: bool = False,  # noqa: FBT001, FBT002
    ) -> None:
        self.max_concurrent = max_concurrent
        self._codex_binary = codex_binary
        self._stream_output = stream_output
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

    async def _read_stream(
        self,
        proc: asyncio.subprocess.Process,
        label: str,
    ) -> str:
        """Read stdout line by line, optionally streaming to terminal."""
        chunks: list[str] = []
        total_chars = 0
        assert proc.stdout is not None  # noqa: S101
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            decoded = line.decode("utf-8", errors="replace")
            total_chars += len(decoded)
            if total_chars <= _MAX_OUTPUT_CHARS:
                chunks.append(decoded)
            if self._stream_output:
                sys.stderr.write(f"  [{label}] {decoded}")
                sys.stderr.flush()
        output = "".join(chunks)
        if total_chars > _MAX_OUTPUT_CHARS:
            output += f"\n[truncated — {total_chars} chars total]"
        return output

    async def spawn(  # noqa: PLR0913
        self,
        task: str,
        cwd: str,
        timeout: float = 300.0,  # noqa: ASYNC109
        system_prompt: str | None = None,
        env_overrides: dict[str, str] | None = None,
        label: str = "",
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
            agent_label = label or task_id
            self._active[task_id] = proc

            try:
                output = await asyncio.wait_for(
                    self._read_stream(proc, agent_label),
                    timeout=timeout,
                )
                await proc.wait()

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
