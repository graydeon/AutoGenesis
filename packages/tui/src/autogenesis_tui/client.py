from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Callable
from typing import Any

import structlog
from websockets.asyncio.client import ClientConnection, connect

logger = structlog.get_logger()


class CodexWSClient:
    """JSON-RPC 2.0 WebSocket client for the codex app-server protocol."""

    def __init__(self, port: int, on_event: Callable[[dict[str, Any]], None]) -> None:
        self._port = port
        self._on_event = on_event
        self._ws: ClientConnection | None = None
        self._pending: dict[str, asyncio.Future[Any]] = {}
        self._active_thread_id: str | None = None
        self._active_turn_id: str | None = None
        self._receive_task: asyncio.Task[None] | None = None

    async def connect(self) -> None:
        uri = f"ws://127.0.0.1:{self._port}"
        self._ws = await connect(uri)
        self._receive_task = asyncio.create_task(self._receive_loop())
        await self._request("initialize", {
            "clientInfo": {"name": "autogenesis-tui", "version": "0.1.0"},
        })
        logger.info("codex_ws_connected", port=self._port)

    async def _receive_loop(self) -> None:
        if self._ws is None:
            return
        try:
            async for raw in self._ws:
                data: dict[str, Any] = json.loads(raw)
                msg_id = str(data.get("id", ""))
                if msg_id and msg_id in self._pending:
                    fut = self._pending.pop(msg_id)
                    if "error" in data:
                        fut.set_exception(RuntimeError(str(data["error"])))
                    else:
                        fut.set_result(data.get("result", {}))
                elif "method" in data:
                    self._handle_notification(data)
        except Exception as exc:
            logger.warning("codex_ws_receive_error", exc=str(exc))

    def _handle_notification(self, data: dict[str, Any]) -> None:
        method = data.get("method", "")
        params = data.get("params", {})
        if method == "turn/started":
            turn = params.get("turn", {})
            self._active_turn_id = turn.get("id")
        elif method == "turn/completed":
            self._active_turn_id = None
        self._on_event({"method": method, "params": params})

    async def _request(self, method: str, params: dict[str, Any]) -> Any:
        if self._ws is None:
            raise RuntimeError("WebSocket not connected. Call connect() first.")
        req_id = uuid.uuid4().hex
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[Any] = loop.create_future()
        self._pending[req_id] = fut
        await self._ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }))
        return await asyncio.wait_for(fut, timeout=30.0)

    async def start_thread(
        self,
        base_instructions: str | None = None,
        cwd: str | None = None,
    ) -> str:
        """Start a new thread. Returns the thread ID."""
        params: dict[str, Any] = {"approvalPolicy": "never"}
        if base_instructions:
            params["baseInstructions"] = base_instructions
        if cwd:
            params["cwd"] = cwd
        result = await self._request("thread/start", params)
        thread = result.get("thread", result)
        self._active_thread_id = thread.get("id", "")
        return self._active_thread_id

    async def send_turn(self, thread_id: str, text: str) -> None:
        """Send a user turn."""
        await self._request("turn/start", {
            "threadId": thread_id,
            "input": [{"type": "text", "text": text}],
        })

    async def interrupt(self, thread_id: str) -> None:
        """Interrupt the active turn."""
        if self._active_turn_id is None:
            return
        await self._request("turn/interrupt", {
            "threadId": thread_id,
            "turnId": self._active_turn_id,
        })

    async def fork_thread(self, thread_id: str) -> str:
        """Fork a thread. Returns new thread ID."""
        result = await self._request("thread/fork", {"threadId": thread_id})
        thread = result.get("thread", result)
        new_id: str = thread.get("id", "")
        return new_id

    async def disconnect(self) -> None:
        if self._receive_task:
            self._receive_task.cancel()
        if self._ws:
            await self._ws.close()
        logger.info("codex_ws_disconnected")

    @property
    def active_thread_id(self) -> str | None:
        return self._active_thread_id

    @property
    def active_turn_id(self) -> str | None:
        return self._active_turn_id
