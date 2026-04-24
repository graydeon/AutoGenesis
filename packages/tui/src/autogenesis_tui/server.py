from __future__ import annotations

import asyncio
import socket
from typing import cast

import structlog

logger = structlog.get_logger()

_STARTUP_WAIT_SECONDS = 0.8
_DEFAULT_APPROVAL_POLICY = "on-request"
_DEFAULT_SANDBOX_MODE = "workspace-write"


class AppServerManager:
    """Manages the lifecycle of a `codex app-server` subprocess."""

    def __init__(
        self,
        *,
        approval_policy: str = _DEFAULT_APPROVAL_POLICY,
        sandbox_mode: str = _DEFAULT_SANDBOX_MODE,
    ) -> None:
        self._process: asyncio.subprocess.Process | None = None
        self._port: int = 0
        self._approval_policy = approval_policy
        self._sandbox_mode = sandbox_mode

    @staticmethod
    def _find_free_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return cast("int", s.getsockname()[1])

    async def start(self) -> int:
        """Spawn codex app-server. Returns the bound port."""
        self._port = self._find_free_port()
        self._process = await asyncio.create_subprocess_exec(
            "codex",
            "app-server",
            "-c",
            f'approval_policy="{self._approval_policy}"',
            "-c",
            f'sandbox_mode="{self._sandbox_mode}"',
            "--listen",
            f"ws://127.0.0.1:{self._port}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.sleep(_STARTUP_WAIT_SECONDS)
        logger.info("app_server_started", port=self._port, pid=self._process.pid)
        return self._port

    async def stop(self) -> None:
        """Terminate the app-server process."""
        if self._process is None:
            return
        self._process.terminate()
        try:
            await asyncio.wait_for(self._process.wait(), timeout=5.0)
        except TimeoutError:
            self._process.kill()
        logger.info("app_server_stopped")
        self._process = None

    @property
    def port(self) -> int:
        return self._port

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.returncode is None
