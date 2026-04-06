"""GitNexus context provider for employee prompts."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

import structlog

logger = structlog.get_logger()


class GitNexusContextProvider:
    """Fetch compact, task-specific codebase context from GitNexus."""

    def __init__(  # noqa: PLR0913
        self,
        enabled: bool = True,  # noqa: FBT001, FBT002
        binary: str = "gitnexus",
        auto_index: bool = True,  # noqa: FBT001, FBT002
        query_limit: int = 3,
        max_context_chars: int = 3000,
        command_timeout_seconds: float = 20.0,
        index_timeout_seconds: float = 600.0,
    ) -> None:
        self._enabled = enabled
        self._binary = binary
        self._auto_index = auto_index
        self._query_limit = query_limit
        self._max_context_chars = max_context_chars
        self._command_timeout = command_timeout_seconds
        self._index_timeout = index_timeout_seconds
        self._binary_available: bool | None = None
        self._repo_ready: dict[str, bool] = {}
        self._task_cache: dict[tuple[str, str], str | None] = {}

    def _is_enabled(self) -> bool:
        return self._enabled

    def _check_binary(self) -> bool:
        if self._binary_available is None:
            self._binary_available = shutil.which(self._binary) is not None
            if not self._binary_available:
                logger.info("gitnexus_binary_missing", binary=self._binary)
        return self._binary_available

    async def _run(self, args: list[str], cwd: Path, deadline_seconds: float) -> tuple[int, str]:
        proc = await asyncio.create_subprocess_exec(
            *args,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=deadline_seconds)
        except TimeoutError:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except TimeoutError:
                proc.kill()
            return 124, "Timed out"

        return proc.returncode or 0, out.decode("utf-8", errors="replace")

    async def _ensure_index_ready(self, cwd: Path) -> bool:
        repo = str(cwd.resolve())
        if repo in self._repo_ready:
            return self._repo_ready[repo]

        code, status_out = await self._run(
            [self._binary, "status"],
            cwd=cwd,
            deadline_seconds=self._command_timeout,
        )
        status_lower = status_out.lower()
        needs_index = code != 0 or "not indexed" in status_lower
        if needs_index and self._auto_index:
            logger.info("gitnexus_auto_index_start", repo=repo)
            analyze_code, analyze_out = await self._run(
                [self._binary, "analyze", str(cwd)],
                cwd=cwd,
                deadline_seconds=self._index_timeout,
            )
            ready = analyze_code == 0
            if not ready:
                logger.warning(
                    "gitnexus_auto_index_failed",
                    repo=repo,
                    output=analyze_out[:500],
                )
            self._repo_ready[repo] = ready
            return ready

        ready = not needs_index
        self._repo_ready[repo] = ready
        return ready

    async def get_task_context(self, task: str, cwd: str | Path) -> str | None:
        """Return concise GitNexus context for a task, or None if unavailable."""
        if not self._is_enabled() or not task.strip() or not self._check_binary():
            return None

        repo = Path(cwd).resolve()
        cache_key = (str(repo), task.strip())
        if cache_key in self._task_cache:
            return self._task_cache[cache_key]

        if not await self._ensure_index_ready(repo):
            self._task_cache[cache_key] = None
            return None

        code, out = await self._run(
            [
                self._binary,
                "query",
                "--repo",
                repo.name,
                "--limit",
                str(self._query_limit),
                task,
            ],
            cwd=repo,
            deadline_seconds=self._command_timeout,
        )
        if code != 0:
            logger.warning("gitnexus_query_failed", repo=str(repo), output=out[:500])
            self._task_cache[cache_key] = None
            return None

        compact = out.strip()
        if not compact:
            self._task_cache[cache_key] = None
            return None
        if len(compact) > self._max_context_chars:
            compact = compact[: self._max_context_chars].rstrip() + "\n…[truncated]"

        context = (
            "## GitNexus Code Context\n\n"
            "Use this as the canonical map of relevant flows/symbols for this task. "
            "Prefer it over broad repo scans.\n\n"
            f"{compact}"
        )
        self._task_cache[cache_key] = context
        return context
