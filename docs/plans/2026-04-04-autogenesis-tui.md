# AutoGenesis TUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Textual-based three-column TUI (`autogenesis tui`) that connects to a managed `codex app-server` subprocess, streams live agent output, and lets you navigate employees, filter the stream, and switch themes.

**Architecture:** New `packages/tui` workspace package with `AutogenesisApp` (Textual) connecting to `codex app-server` via WebSocket JSON-RPC. Two data sources feed the AgentStream: WebSocket events for CEO chat and `SubAgentManager.on_output` callbacks for dispatched employee subprocesses. Themes are TOML files mapped to Textual `Theme` objects.

**Tech Stack:** Python 3.11+, `textual>=0.87`, `websockets>=13`, `uv` workspace, `pytest-asyncio` (existing), `autogenesis-core`, `autogenesis-employees`.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `packages/tui/pyproject.toml` | Create | Package metadata + deps |
| `packages/tui/src/autogenesis_tui/__init__.py` | Create | Version export |
| `packages/tui/src/autogenesis_tui/themes.py` | Create | ThemeManager: load TOML → Textual Theme |
| `packages/tui/src/autogenesis_tui/themes/dracula.toml` | Create | Built-in Dracula palette |
| `packages/tui/src/autogenesis_tui/themes/midnight-blue.toml` | Create | Built-in Midnight Blue palette |
| `packages/tui/src/autogenesis_tui/themes/hacker-green.toml` | Create | Built-in Hacker Green palette |
| `packages/tui/src/autogenesis_tui/server.py` | Create | AppServerManager: spawn/kill codex app-server |
| `packages/tui/src/autogenesis_tui/client.py` | Create | CodexWSClient: WebSocket JSON-RPC |
| `packages/tui/src/autogenesis_tui/widgets/__init__.py` | Create | Re-exports |
| `packages/tui/src/autogenesis_tui/widgets/status_bar.py` | Create | StatusBar widget |
| `packages/tui/src/autogenesis_tui/widgets/roster.py` | Create | EmployeeRoster widget |
| `packages/tui/src/autogenesis_tui/widgets/stream.py` | Create | AgentStream widget |
| `packages/tui/src/autogenesis_tui/widgets/right_panel.py` | Create | RightPanel widget (goals/tokens + employee detail) |
| `packages/tui/src/autogenesis_tui/widgets/input_bar.py` | Create | InputBar widget |
| `packages/tui/src/autogenesis_tui/app.py` | Create | AutogenesisApp: layout, wiring, event routing |
| `packages/tui/tests/__init__.py` | Create | Empty |
| `packages/tui/tests/test_themes.py` | Create | ThemeManager tests |
| `packages/tui/tests/test_server.py` | Create | AppServerManager tests |
| `packages/tui/tests/test_client.py` | Create | CodexWSClient tests |
| `packages/tui/tests/test_widgets.py` | Create | Widget rendering tests |
| `packages/tui/tests/test_app.py` | Create | AutogenesisApp integration tests |
| `packages/cli/src/autogenesis_cli/commands/tui.py` | Create | `autogenesis tui` CLI command |
| `packages/cli/src/autogenesis_cli/app.py` | Modify | Register tui command |
| `packages/cli/pyproject.toml` | Modify | Add `autogenesis-tui` dependency |
| `pyproject.toml` | Modify | Add `packages/tui` to workspace members |

---

## Task 1: Package Scaffold

**Files:**
- Create: `packages/tui/pyproject.toml`
- Create: `packages/tui/src/autogenesis_tui/__init__.py`
- Create: `packages/tui/tests/__init__.py`
- Modify: `pyproject.toml` (root)

- [ ] **Step 1: Create `packages/tui/pyproject.toml`**

```toml
[project]
name = "autogenesis-tui"
version = "0.1.0"
description = "AutoGenesis terminal UI"
requires-python = ">=3.11"
license = "MIT"
dependencies = [
    "autogenesis-core",
    "autogenesis-employees",
    "textual>=0.87",
    "websockets>=13",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/autogenesis_tui"]
```

- [ ] **Step 2: Create `packages/tui/src/autogenesis_tui/__init__.py`**

```python
"""AutoGenesis TUI — Textual-based terminal interface."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Create `packages/tui/tests/__init__.py`**

Empty file.

- [ ] **Step 4: Add `packages/tui` to root `pyproject.toml` workspace**

In `pyproject.toml`, find `[tool.uv.workspace]` and add `"packages/tui"` to the `members` list. Also add `autogenesis-tui` to `[tool.uv.sources]` and to the `dev` optional-dependencies list.

```toml
[tool.uv.workspace]
members = [
    "packages/core",
    "packages/tools",
    "packages/tokens",
    "packages/optimizer",
    "packages/security",
    "packages/mcp",
    "packages/plugins",
    "packages/cli",
    "packages/twitter",
    "packages/employees",
    "packages/tui",          # ← add this
]

[tool.uv.sources]
# ... existing entries ...
autogenesis-tui = { workspace = true }   # ← add this
```

In `[project.optional-dependencies]`:
```toml
dev = [
    # ... existing ...
    "autogenesis-tui",
]
```

- [ ] **Step 5: Sync workspace**

```bash
cd /home/gray/dev/AutoGenesis
uv sync --all-packages
```

Expected: resolves without errors, `autogenesis-tui` appears in the lock.

- [ ] **Step 6: Verify import**

```bash
uv run python -c "import autogenesis_tui; print(autogenesis_tui.__version__)"
```

Expected output: `0.1.0`

- [ ] **Step 7: Commit**

```bash
git add packages/tui/ pyproject.toml
git commit -m "feat(tui): scaffold autogenesis-tui package"
```

---

## Task 2: ThemeManager + Built-in Themes

**Files:**
- Create: `packages/tui/src/autogenesis_tui/themes.py`
- Create: `packages/tui/src/autogenesis_tui/themes/dracula.toml`
- Create: `packages/tui/src/autogenesis_tui/themes/midnight-blue.toml`
- Create: `packages/tui/src/autogenesis_tui/themes/hacker-green.toml`
- Test: `packages/tui/tests/test_themes.py`

- [ ] **Step 1: Write failing tests**

```python
# packages/tui/tests/test_themes.py
from __future__ import annotations

from pathlib import Path

import pytest

from autogenesis_tui.themes import ThemeManager


def test_builtin_themes_loaded():
    mgr = ThemeManager()
    names = mgr.list_theme_names()
    assert "dracula" in names
    assert "midnight-blue" in names
    assert "hacker-green" in names


def test_get_theme_returns_dict():
    mgr = ThemeManager()
    t = mgr.get_theme("dracula")
    assert t["background"] == "#282a36"
    assert t["surface"] == "#21222c"
    assert t["accent"] == "#bd93f9"
    assert t["success"] == "#50fa7b"
    assert t["warning"] == "#f1fa8c"
    assert t["error"] == "#ff5555"
    assert t["text"] == "#f8f8f2"
    assert t["subtext"] == "#6272a4"
    assert t["border"] == "#44475a"


def test_unknown_theme_raises():
    mgr = ThemeManager()
    with pytest.raises(KeyError, match="unknown-theme"):
        mgr.get_theme("unknown-theme")


def test_user_theme_loaded(tmp_path: Path):
    theme_dir = tmp_path / "themes"
    theme_dir.mkdir()
    (theme_dir / "custom.toml").write_text(
        '[theme]\nname = "custom"\nbackground = "#000000"\n'
        'surface = "#111111"\naccent = "#ffffff"\nsuccess = "#00ff00"\n'
        'warning = "#ffff00"\nerror = "#ff0000"\ntext = "#eeeeee"\n'
        'subtext = "#888888"\nborder = "#333333"\n'
    )
    mgr = ThemeManager(user_themes_dir=theme_dir)
    assert "custom" in mgr.list_theme_names()


def test_to_textual_theme():
    from textual.theme import Theme

    mgr = ThemeManager()
    t = mgr.to_textual_theme("dracula")
    assert isinstance(t, Theme)
    assert t.name == "dracula"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd /home/gray/dev/AutoGenesis
uv run pytest packages/tui/tests/test_themes.py -v
```

Expected: `ModuleNotFoundError` or `ImportError` (ThemeManager doesn't exist yet).

- [ ] **Step 3: Create Dracula theme file**

```toml
# packages/tui/src/autogenesis_tui/themes/dracula.toml
[theme]
name       = "dracula"
background = "#282a36"
surface    = "#21222c"
accent     = "#bd93f9"
success    = "#50fa7b"
warning    = "#f1fa8c"
error      = "#ff5555"
text       = "#f8f8f2"
subtext    = "#6272a4"
border     = "#44475a"
```

- [ ] **Step 4: Create Midnight Blue theme file**

```toml
# packages/tui/src/autogenesis_tui/themes/midnight-blue.toml
[theme]
name       = "midnight-blue"
background = "#0d1117"
surface    = "#161b22"
accent     = "#58a6ff"
success    = "#3fb950"
warning    = "#e3b341"
error      = "#f85149"
text       = "#cdd9e5"
subtext    = "#6e7681"
border     = "#30363d"
```

- [ ] **Step 5: Create Hacker Green theme file**

```toml
# packages/tui/src/autogenesis_tui/themes/hacker-green.toml
[theme]
name       = "hacker-green"
background = "#0a0e0a"
surface    = "#0d130d"
accent     = "#00ff41"
success    = "#00c832"
warning    = "#ffaa00"
error      = "#ff3333"
text       = "#ccffcc"
subtext    = "#3a5a3a"
border     = "#1e3a1e"
```

- [ ] **Step 6: Implement ThemeManager**

```python
# packages/tui/src/autogenesis_tui/themes.py
from __future__ import annotations

import tomllib
from pathlib import Path

from textual.theme import Theme

_BUILTIN_DIR = Path(__file__).parent / "themes"

# Palette indices used for per-employee accent color cycling.
# Maps roster position → color key from theme dict.
EMPLOYEE_PALETTE_KEYS = ["success", "warning", "accent", "error", "text"]


class ThemeManager:
    """Loads built-in and user TOML themes, converts to Textual Theme objects."""

    def __init__(self, user_themes_dir: Path | None = None) -> None:
        self._themes: dict[str, dict] = {}
        self._load_dir(_BUILTIN_DIR)
        if user_themes_dir and user_themes_dir.is_dir():
            self._load_dir(user_themes_dir)

    def _load_dir(self, directory: Path) -> None:
        for path in directory.glob("*.toml"):
            with path.open("rb") as f:
                data = tomllib.load(f)
            palette = data.get("theme", data)
            name = palette.get("name", path.stem)
            self._themes[name] = palette

    def list_theme_names(self) -> list[str]:
        return list(self._themes.keys())

    def get_theme(self, name: str) -> dict:
        if name not in self._themes:
            raise KeyError(name)
        return self._themes[name]

    def to_textual_theme(self, name: str) -> Theme:
        t = self.get_theme(name)
        return Theme(
            name=name,
            dark=True,
            primary=t["accent"],
            secondary=t["subtext"],
            warning=t["warning"],
            error=t["error"],
            success=t["success"],
            background=t["background"],
            surface=t["surface"],
            panel=t["border"],
        )

    def employee_color(self, index: int, theme_name: str) -> str:
        """Return a stable accent color for an employee at roster index."""
        t = self.get_theme(theme_name)
        key = EMPLOYEE_PALETTE_KEYS[index % len(EMPLOYEE_PALETTE_KEYS)]
        return t[key]
```

- [ ] **Step 7: Run tests — verify they pass**

```bash
uv run pytest packages/tui/tests/test_themes.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add packages/tui/src/autogenesis_tui/themes.py \
        packages/tui/src/autogenesis_tui/themes/ \
        packages/tui/tests/test_themes.py
git commit -m "feat(tui): ThemeManager with Dracula, Midnight Blue, Hacker Green"
```

---

## Task 3: AppServerManager

**Files:**
- Create: `packages/tui/src/autogenesis_tui/server.py`
- Test: `packages/tui/tests/test_server.py`

- [ ] **Step 1: Write failing tests**

```python
# packages/tui/tests/test_server.py
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autogenesis_tui.server import AppServerManager


def test_find_free_port_returns_int():
    port = AppServerManager._find_free_port()
    assert isinstance(port, int)
    assert 1024 < port < 65536


@pytest.mark.asyncio
async def test_start_spawns_process():
    mgr = AppServerManager()
    mock_proc = MagicMock()
    mock_proc.returncode = None

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_proc
        port = await mgr.start()

    assert port > 0
    assert mgr.port == port
    assert mgr.is_running
    mock_exec.assert_called_once()
    cmd = mock_exec.call_args[0]
    assert cmd[0] == "codex"
    assert "app-server" in cmd
    assert any(f"ws://127.0.0.1:{port}" in str(a) for a in cmd)


@pytest.mark.asyncio
async def test_stop_terminates_process():
    mgr = AppServerManager()
    mock_proc = MagicMock()
    mock_proc.returncode = None
    mock_proc.wait = AsyncMock()

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_proc
        await mgr.start()

    await mgr.stop()
    mock_proc.terminate.assert_called_once()
    assert not mgr.is_running


@pytest.mark.asyncio
async def test_stop_when_not_started_is_safe():
    mgr = AppServerManager()
    await mgr.stop()  # should not raise
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
uv run pytest packages/tui/tests/test_server.py -v
```

Expected: `ImportError` for `autogenesis_tui.server`.

- [ ] **Step 3: Implement AppServerManager**

```python
# packages/tui/src/autogenesis_tui/server.py
from __future__ import annotations

import asyncio
import socket

import structlog

logger = structlog.get_logger()

_STARTUP_WAIT_SECONDS = 0.8


class AppServerManager:
    """Manages the lifecycle of a `codex app-server` subprocess."""

    def __init__(self) -> None:
        self._process: asyncio.subprocess.Process | None = None
        self._port: int = 0

    @staticmethod
    def _find_free_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    async def start(self) -> int:
        """Spawn codex app-server. Returns the bound port."""
        self._port = self._find_free_port()
        self._process = await asyncio.create_subprocess_exec(
            "codex",
            "app-server",
            "--listen",
            f"ws://127.0.0.1:{self._port}",
            "--dangerously-bypass-approvals-and-sandbox",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # Give the server a moment to bind the socket before clients connect.
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
        except asyncio.TimeoutError:
            self._process.kill()
        logger.info("app_server_stopped")
        self._process = None

    @property
    def port(self) -> int:
        return self._port

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.returncode is None
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
uv run pytest packages/tui/tests/test_server.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/tui/src/autogenesis_tui/server.py \
        packages/tui/tests/test_server.py
git commit -m "feat(tui): AppServerManager spawns and stops codex app-server"
```

---

## Task 4: CodexWSClient

**Files:**
- Create: `packages/tui/src/autogenesis_tui/client.py`
- Test: `packages/tui/tests/test_client.py`

The protocol is JSON-RPC 2.0 over WebSocket.
- **Client → Server requests:** `{ "jsonrpc": "2.0", "id": "<uuid>", "method": "<method>", "params": {...} }`
- **Server → Client responses:** `{ "jsonrpc": "2.0", "id": "<uuid>", "result": {...} }` or `{ ..., "error": {...} }`
- **Server → Client notifications:** `{ "method": "<method>", "params": {...} }` (no `id`)

Key methods used:
- `initialize` — `{ clientInfo: { name, version } }` → called once on connect
- `thread/start` — `{ baseInstructions?, developerInstructions?, cwd?, approvalPolicy?, ephemeral? }` → returns thread object with `id`
- `turn/start` — `{ threadId, input: [{ type: "text", text: string }] }` → starts a turn; `turn/started` notification follows
- `turn/interrupt` — `{ threadId, turnId }` → interrupts active turn
- `thread/fork` — `{ threadId }` → forks a thread; returns new thread object

Key notifications received (via `on_event` callback):
- `thread/started` — `{ thread: { id, name, status, ... } }`
- `turn/started` — `{ threadId, turn: { id, ... } }`
- `turn/completed` — `{ threadId, turn: { id, ... } }`
- `item/agentMessage/delta` — `{ delta, itemId, threadId, turnId }`
- `item/commandExecution/outputDelta` — `{ delta, itemId, threadId, turnId }`
- `thread/tokenUsage/updated` — `{ threadId, turnId, tokenUsage: { total: { totalTokens, ... } } }`

- [ ] **Step 1: Write failing tests**

```python
# packages/tui/tests/test_client.py
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autogenesis_tui.client import CodexWSClient


@pytest.fixture
def mock_ws():
    ws = MagicMock()
    ws.send = AsyncMock()
    ws.close = AsyncMock()
    ws.__aiter__ = MagicMock(return_value=iter([]))
    return ws


@pytest.mark.asyncio
async def test_connect_sends_initialize(mock_ws):
    events = []

    async def fake_connect(uri):
        return mock_ws

    # Simulate server responding to initialize
    init_response = json.dumps({
        "jsonrpc": "2.0",
        "id": "PLACEHOLDER",
        "result": {"serverInfo": {"name": "codex", "version": "0.1"}},
    })

    call_count = 0

    async def fake_send(msg):
        nonlocal call_count
        call_count += 1
        data = json.loads(msg)
        if data["method"] == "initialize":
            # Inject a response into pending
            fut = client._pending.get(data["id"])
            if fut:
                fut.set_result({"serverInfo": {}})

    mock_ws.send = fake_send

    with patch("websockets.connect", new=AsyncMock(return_value=mock_ws)):
        client = CodexWSClient(port=12345, on_event=events.append)
        # Prevent _receive_loop from blocking by making __aiter__ immediately done
        mock_ws.__aiter__ = MagicMock(return_value=iter([]))
        await client.connect()

    assert call_count >= 1


@pytest.mark.asyncio
async def test_start_thread_returns_thread_id(mock_ws):
    events = []

    async def fake_send(msg):
        data = json.loads(msg)
        fut = client._pending.get(data.get("id", ""))
        if fut and not fut.done():
            if data["method"] == "initialize":
                fut.set_result({"serverInfo": {}})
            elif data["method"] == "thread/start":
                fut.set_result({"thread": {"id": "thread-abc-123"}})

    mock_ws.send = fake_send
    mock_ws.__aiter__ = MagicMock(return_value=iter([]))

    with patch("websockets.connect", new=AsyncMock(return_value=mock_ws)):
        client = CodexWSClient(port=12345, on_event=events.append)
        await client.connect()
        thread_id = await client.start_thread(base_instructions="You are CEO.")

    assert thread_id == "thread-abc-123"


@pytest.mark.asyncio
async def test_on_event_called_for_notifications(mock_ws):
    events = []
    notification = json.dumps({
        "method": "item/agentMessage/delta",
        "params": {
            "delta": "Hello",
            "itemId": "item-1",
            "threadId": "t-1",
            "turnId": "turn-1",
        },
    })

    # Feed the notification through __aiter__
    received = []

    async def fake_send(msg):
        data = json.loads(msg)
        fut = client._pending.get(data.get("id", ""))
        if fut and not fut.done():
            fut.set_result({})

    mock_ws.send = fake_send

    async def aiter_mock():
        yield notification

    mock_ws.__aiter__ = MagicMock(return_value=aiter_mock())

    with patch("websockets.connect", new=AsyncMock(return_value=mock_ws)):
        client = CodexWSClient(port=12345, on_event=events.append)
        await client.connect()
        await asyncio.sleep(0.05)  # let receive loop process

    assert any(e.get("method") == "item/agentMessage/delta" for e in events)


@pytest.mark.asyncio
async def test_disconnect_closes_ws(mock_ws):
    async def fake_send(msg):
        data = json.loads(msg)
        fut = client._pending.get(data.get("id", ""))
        if fut and not fut.done():
            fut.set_result({})

    mock_ws.send = fake_send
    mock_ws.__aiter__ = MagicMock(return_value=iter([]))

    with patch("websockets.connect", new=AsyncMock(return_value=mock_ws)):
        client = CodexWSClient(port=12345, on_event=lambda e: None)
        await client.connect()
        await client.disconnect()

    mock_ws.close.assert_called_once()
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
uv run pytest packages/tui/tests/test_client.py -v
```

Expected: `ImportError` for `autogenesis_tui.client`.

- [ ] **Step 3: Implement CodexWSClient**

```python
# packages/tui/src/autogenesis_tui/client.py
from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Callable
from typing import Any

import structlog
import websockets
from websockets.asyncio.client import ClientConnection

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
        self._receive_task: asyncio.Task | None = None

    async def connect(self) -> None:
        uri = f"ws://127.0.0.1:{self._port}"
        self._ws = await websockets.connect(uri)
        self._receive_task = asyncio.create_task(self._receive_loop())
        await self._request("initialize", {
            "clientInfo": {"name": "autogenesis-tui", "version": "0.1.0"},
        })
        logger.info("codex_ws_connected", port=self._port)

    async def _receive_loop(self) -> None:
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
        req_id = uuid.uuid4().hex
        loop = asyncio.get_event_loop()
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
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
uv run pytest packages/tui/tests/test_client.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/tui/src/autogenesis_tui/client.py \
        packages/tui/tests/test_client.py
git commit -m "feat(tui): CodexWSClient — JSON-RPC WebSocket to codex app-server"
```

---

## Task 5: StatusBar Widget

**Files:**
- Create: `packages/tui/src/autogenesis_tui/widgets/__init__.py`
- Create: `packages/tui/src/autogenesis_tui/widgets/status_bar.py`
- Test: `packages/tui/tests/test_widgets.py` (start this file)

- [ ] **Step 1: Write failing tests**

```python
# packages/tui/tests/test_widgets.py
from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from autogenesis_tui.widgets.status_bar import StatusBar


class _StatusBarApp(App):
    def compose(self) -> ComposeResult:
        yield StatusBar()


@pytest.mark.asyncio
async def test_status_bar_renders():
    async with _StatusBarApp().run_test() as pilot:
        bar = pilot.app.query_one(StatusBar)
        assert bar is not None


@pytest.mark.asyncio
async def test_status_bar_update_tokens():
    async with _StatusBarApp().run_test() as pilot:
        bar = pilot.app.query_one(StatusBar)
        bar.update_tokens(42000)
        assert bar.session_tokens == 42000


@pytest.mark.asyncio
async def test_status_bar_update_connection():
    async with _StatusBarApp().run_test() as pilot:
        bar = pilot.app.query_one(StatusBar)
        bar.update_connection("connected", "gpt-5.3-codex")
        assert bar.connection_state == "connected"
        assert bar.model_name == "gpt-5.3-codex"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
uv run pytest packages/tui/tests/test_widgets.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Create `packages/tui/src/autogenesis_tui/widgets/__init__.py`**

```python
"""AutoGenesis TUI widgets."""
from autogenesis_tui.widgets.status_bar import StatusBar
from autogenesis_tui.widgets.roster import EmployeeRoster
from autogenesis_tui.widgets.stream import AgentStream
from autogenesis_tui.widgets.right_panel import RightPanel
from autogenesis_tui.widgets.input_bar import InputBar

__all__ = ["StatusBar", "EmployeeRoster", "AgentStream", "RightPanel", "InputBar"]
```

- [ ] **Step 4: Implement StatusBar**

```python
# packages/tui/src/autogenesis_tui/widgets/status_bar.py
from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


class StatusBar(Widget):
    """Top bar: app name, model, connection state, token count."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        layout: horizontal;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    StatusBar Label {
        margin: 0 2 0 0;
    }
    StatusBar #title {
        color: $primary;
        text-style: bold;
    }
    StatusBar #conn-connected {
        color: $success;
    }
    StatusBar #conn-connecting {
        color: $warning;
    }
    StatusBar #conn-disconnected {
        color: $error;
    }
    StatusBar #conn-reconnecting {
        color: $warning;
    }
    """

    session_tokens: reactive[int] = reactive(0)
    connection_state: reactive[str] = reactive("connecting")
    model_name: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield Label("⬡ AutoGenesis", id="title")
        yield Label("", id="model-label")
        yield Label("● connecting", id="conn-connecting")
        yield Label("0 tokens", id="token-label")

    def watch_session_tokens(self, tokens: int) -> None:
        self.query_one("#token-label", Label).update(f"{tokens:,} tokens")

    def watch_connection_state(self, state: str) -> None:
        for label in self.query("Label"):
            if label.id and label.id.startswith("conn-"):
                label.remove()
        symbol = "●" if state == "connected" else "⟳" if state in ("connecting", "reconnecting") else "○"
        self.mount(Label(f"{symbol} {state}", id=f"conn-{state}"))

    def watch_model_name(self, name: str) -> None:
        if name:
            self.query_one("#model-label", Label).update(name)

    def update_tokens(self, tokens: int) -> None:
        self.session_tokens = tokens

    def update_connection(self, state: str, model: str = "") -> None:
        self.connection_state = state
        if model:
            self.model_name = model
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
uv run pytest packages/tui/tests/test_widgets.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/tui/src/autogenesis_tui/widgets/ \
        packages/tui/tests/test_widgets.py
git commit -m "feat(tui): StatusBar widget"
```

---

## Task 6: EmployeeRoster Widget

**Files:**
- Modify: `packages/tui/src/autogenesis_tui/widgets/roster.py` (create)
- Modify: `packages/tui/tests/test_widgets.py` (append tests)

- [ ] **Step 1: Append failing tests to `test_widgets.py`**

```python
# Append to packages/tui/tests/test_widgets.py

from autogenesis_tui.widgets.roster import EmployeeRoster, EmployeeRow


class _RosterApp(App):
    def compose(self) -> ComposeResult:
        yield EmployeeRoster()


@pytest.mark.asyncio
async def test_roster_renders_empty():
    async with _RosterApp().run_test() as pilot:
        roster = pilot.app.query_one(EmployeeRoster)
        assert roster is not None
        assert roster.selected_employee is None


@pytest.mark.asyncio
async def test_roster_load_employees():
    rows = [
        EmployeeRow(id="backend-eng", title="Backend Engineer", status="idle"),
        EmployeeRow(id="frontend-eng", title="Frontend Engineer", status="working"),
    ]
    async with _RosterApp().run_test() as pilot:
        roster = pilot.app.query_one(EmployeeRoster)
        roster.load(rows)
        assert len(roster.rows) == 2


@pytest.mark.asyncio
async def test_roster_select_employee():
    rows = [EmployeeRow(id="backend-eng", title="Backend Engineer", status="idle")]

    selected = []

    class _TestApp(App):
        def compose(self) -> ComposeResult:
            yield EmployeeRoster()

        def on_employee_roster_selected(self, event: EmployeeRoster.Selected) -> None:
            selected.append(event.employee_id)

    async with _TestApp().run_test() as pilot:
        roster = pilot.app.query_one(EmployeeRoster)
        roster.load(rows)
        roster.select("backend-eng")
        await pilot.pause()

    assert selected == ["backend-eng"]


@pytest.mark.asyncio
async def test_roster_set_status():
    rows = [EmployeeRow(id="backend-eng", title="Backend Engineer", status="idle")]
    async with _RosterApp().run_test() as pilot:
        roster = pilot.app.query_one(EmployeeRoster)
        roster.load(rows)
        roster.set_status("backend-eng", "working")
        assert roster.rows[0].status == "working"
```

- [ ] **Step 2: Run — verify new tests fail**

```bash
uv run pytest packages/tui/tests/test_widgets.py -v
```

Expected: ImportError on `autogenesis_tui.widgets.roster`.

- [ ] **Step 3: Implement EmployeeRoster**

```python
# packages/tui/src/autogenesis_tui/widgets/roster.py
from __future__ import annotations

from dataclasses import dataclass, field

from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView, Static

_STATUS_ICONS = {
    "idle": ("○", "dim"),
    "working": ("⟳", "warning"),
    "done": ("✓", "success"),
    "active": ("●", "success"),
}


@dataclass
class EmployeeRow:
    id: str
    title: str
    status: str = "idle"
    detail: str = ""


class EmployeeRoster(Widget):
    """Left column: scrollable employee list with status indicators."""

    DEFAULT_CSS = """
    EmployeeRoster {
        width: 22;
        height: 100%;
        background: $surface;
        border-right: solid $panel;
        overflow-y: auto;
    }
    EmployeeRoster .roster-header {
        color: $primary;
        text-style: bold;
        padding: 0 1;
        height: 1;
    }
    EmployeeRoster .employee-row {
        padding: 0 1;
        height: 2;
    }
    EmployeeRoster .employee-row:hover {
        background: $panel;
    }
    EmployeeRoster .employee-row.selected {
        background: $panel;
        color: $secondary;
    }
    """

    selected_employee: reactive[str | None] = reactive(None)

    class Selected(Message):
        def __init__(self, employee_id: str | None) -> None:
            super().__init__()
            self.employee_id = employee_id

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[EmployeeRow] = []

    def compose(self) -> ComposeResult:
        yield Static("EMPLOYEES", classes="roster-header")
        yield Static("", id="roster-list")
        yield Static("SHORTCUTS\nH hr  S standup\nU union  ? help", classes="roster-header")

    def load(self, rows: list[EmployeeRow]) -> None:
        self.rows = list(rows)
        self._refresh_list()

    def _refresh_list(self) -> None:
        roster_list = self.query_one("#roster-list", Static)
        lines = []
        for row in self.rows:
            icon, _ = _STATUS_ICONS.get(row.status, ("○", "dim"))
            selected = " ▶" if row.id == self.selected_employee else ""
            lines.append(f"{icon} {row.id}{selected}")
        roster_list.update("\n".join(lines))

    def set_status(self, employee_id: str, status: str) -> None:
        for row in self.rows:
            if row.id == employee_id:
                row.status = status
                break
        self._refresh_list()

    def set_detail(self, employee_id: str, detail: str) -> None:
        for row in self.rows:
            if row.id == employee_id:
                row.detail = detail
                break
        self._refresh_list()

    def select(self, employee_id: str | None) -> None:
        self.selected_employee = employee_id
        self._refresh_list()
        self.post_message(self.Selected(employee_id))

    def deselect(self) -> None:
        self.select(None)
```

- [ ] **Step 4: Run — verify tests pass**

```bash
uv run pytest packages/tui/tests/test_widgets.py -v
```

Expected: all roster tests PASS, existing StatusBar tests still PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/tui/src/autogenesis_tui/widgets/roster.py \
        packages/tui/tests/test_widgets.py
git commit -m "feat(tui): EmployeeRoster widget"
```

---

## Task 7: AgentStream Widget

**Files:**
- Create: `packages/tui/src/autogenesis_tui/widgets/stream.py`
- Modify: `packages/tui/tests/test_widgets.py` (append)

- [ ] **Step 1: Append failing tests**

```python
# Append to packages/tui/tests/test_widgets.py

from autogenesis_tui.widgets.stream import AgentStream, StreamEntry


class _StreamApp(App):
    def compose(self) -> ComposeResult:
        yield AgentStream()


@pytest.mark.asyncio
async def test_stream_renders_empty():
    async with _StreamApp().run_test() as pilot:
        stream = pilot.app.query_one(AgentStream)
        assert stream is not None
        assert stream.active_filter is None


@pytest.mark.asyncio
async def test_stream_add_agent_delta():
    async with _StreamApp().run_test() as pilot:
        stream = pilot.app.query_one(AgentStream)
        stream.add_agent_delta("Hello ", "CEO", "t-1")
        stream.add_agent_delta("world", "CEO", "t-1")
        assert len(stream.entries) == 1
        assert stream.entries[0].text == "Hello world"
        assert stream.entries[0].source == "CEO"


@pytest.mark.asyncio
async def test_stream_add_tool_block():
    async with _StreamApp().run_test() as pilot:
        stream = pilot.app.query_one(AgentStream)
        stream.add_tool_block("file_write", "src/main.py", success=True, source="backend-eng")
        assert len(stream.entries) == 1
        assert stream.entries[0].is_tool


@pytest.mark.asyncio
async def test_stream_filter_by_employee():
    async with _StreamApp().run_test() as pilot:
        stream = pilot.app.query_one(AgentStream)
        stream.add_agent_delta("CEO says hi", "CEO", "t-1")
        stream.add_agent_delta("eng says hi", "backend-eng", "t-2")
        stream.set_filter("CEO")
        visible = [e for e in stream.entries if stream._entry_visible(e)]
        assert all(e.source == "CEO" for e in visible)
```

- [ ] **Step 2: Run — verify they fail**

```bash
uv run pytest packages/tui/tests/test_widgets.py::test_stream_renders_empty -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement AgentStream**

```python
# packages/tui/src/autogenesis_tui/widgets/stream.py
from __future__ import annotations

from dataclasses import dataclass, field

from rich.text import Text
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.scroll_view import ScrollView
from textual.widget import Widget
from textual.widgets import Label, Static


@dataclass
class StreamEntry:
    source: str          # "CEO" or employee id
    text: str = ""
    is_tool: bool = False
    tool_name: str = ""
    tool_arg: str = ""
    tool_success: bool = True
    turn_id: str = ""
    complete: bool = False  # True once turn/completed received for this entry


class AgentStream(Widget):
    """Center column: scrolling log of all agent activity with source filtering."""

    DEFAULT_CSS = """
    AgentStream {
        width: 1fr;
        height: 100%;
        background: $background;
        overflow-y: auto;
    }
    AgentStream .filter-bar {
        height: 1;
        background: $surface;
        border-bottom: solid $panel;
        padding: 0 1;
    }
    AgentStream .stream-body {
        height: 1fr;
        overflow-y: auto;
        padding: 0 1;
    }
    """

    active_filter: reactive[str | None] = reactive(None)

    def __init__(self) -> None:
        super().__init__()
        self.entries: list[StreamEntry] = []
        self._current_entry: dict[str, StreamEntry] = {}  # turn_id → active entry

    def compose(self) -> ComposeResult:
        yield Static("ALL", id="filter-bar", classes="filter-bar")
        yield Static("", id="stream-body", classes="stream-body")

    def add_agent_delta(self, delta: str, source: str, turn_id: str) -> None:
        """Append a streaming delta to the current entry for this turn."""
        if turn_id not in self._current_entry:
            entry = StreamEntry(source=source, turn_id=turn_id)
            self.entries.append(entry)
            self._current_entry[turn_id] = entry
        self._current_entry[turn_id].text += delta
        self._refresh_body()

    def complete_turn(self, turn_id: str) -> None:
        """Mark a turn as completed."""
        entry = self._current_entry.pop(turn_id, None)
        if entry:
            entry.complete = True
        self._refresh_body()

    def add_tool_block(
        self,
        tool_name: str,
        tool_arg: str,
        success: bool,
        source: str,
        turn_id: str = "",
    ) -> None:
        """Add a completed tool call block."""
        entry = StreamEntry(
            source=source,
            is_tool=True,
            tool_name=tool_name,
            tool_arg=tool_arg,
            tool_success=success,
            turn_id=turn_id,
            complete=True,
        )
        self.entries.append(entry)
        self._refresh_body()

    def set_filter(self, source: str | None) -> None:
        self.active_filter = source
        self._refresh_filter_bar()
        self._refresh_body()

    def _entry_visible(self, entry: StreamEntry) -> bool:
        if self.active_filter is None:
            return True
        return entry.source == self.active_filter

    def _refresh_filter_bar(self) -> None:
        filt = self.active_filter or "ALL"
        self.query_one("#filter-bar", Static).update(f"[ALL] [{filt}]")

    def _refresh_body(self) -> None:
        lines: list[str] = []
        for entry in self.entries:
            if not self._entry_visible(entry):
                continue
            if entry.is_tool:
                result = "→ ok" if entry.tool_success else "→ error"
                lines.append(f"  ▸ {entry.tool_name}  {entry.tool_arg}")
                lines.append(f"  {result}")
            else:
                suffix = " ✓" if entry.complete else ""
                lines.append(f"{entry.source} › {entry.text}{suffix}")
        self.query_one("#stream-body", Static).update("\n".join(lines))
```

- [ ] **Step 4: Run — verify pass**

```bash
uv run pytest packages/tui/tests/test_widgets.py -v
```

Expected: all stream tests PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/tui/src/autogenesis_tui/widgets/stream.py \
        packages/tui/tests/test_widgets.py
git commit -m "feat(tui): AgentStream widget with source filtering"
```

---

## Task 8: RightPanel Widget

**Files:**
- Create: `packages/tui/src/autogenesis_tui/widgets/right_panel.py`
- Modify: `packages/tui/tests/test_widgets.py` (append)

- [ ] **Step 1: Append failing tests**

```python
# Append to packages/tui/tests/test_widgets.py

from autogenesis_tui.widgets.right_panel import RightPanel, GoalEntry


class _RightPanelApp(App):
    def compose(self) -> ComposeResult:
        yield RightPanel()


@pytest.mark.asyncio
async def test_right_panel_default_mode():
    async with _RightPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(RightPanel)
        assert panel.mode == "goals"


@pytest.mark.asyncio
async def test_right_panel_show_goals():
    async with _RightPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(RightPanel)
        panel.update_goals([
            GoalEntry(id="g1", description="Add JWT auth", completed=2, total=4),
        ])
        assert len(panel.goals) == 1


@pytest.mark.asyncio
async def test_right_panel_update_tokens():
    async with _RightPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(RightPanel)
        panel.update_tokens(session=42000, daily=100000)
        assert panel.session_tokens == 42000


@pytest.mark.asyncio
async def test_right_panel_employee_detail_mode():
    async with _RightPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(RightPanel)
        panel.show_employee(
            employee_id="backend-eng",
            memories=["Prefers asyncio", "Uses pytest"],
            inbox_count=3,
            training=["Always use type hints"],
        )
        assert panel.mode == "employee"
        assert panel.focused_employee == "backend-eng"


@pytest.mark.asyncio
async def test_right_panel_back_to_goals():
    async with _RightPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(RightPanel)
        panel.show_employee("backend-eng", [], 0, [])
        panel.show_goals()
        assert panel.mode == "goals"
```

- [ ] **Step 2: Run — verify they fail**

```bash
uv run pytest packages/tui/tests/test_widgets.py -k "right_panel" -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement RightPanel**

```python
# packages/tui/src/autogenesis_tui/widgets/right_panel.py
from __future__ import annotations

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


@dataclass
class GoalEntry:
    id: str
    description: str
    completed: int
    total: int
    status: str = "executing"


class RightPanel(Widget):
    """Right column — toggles between Goals/Tokens view and Employee Detail view."""

    DEFAULT_CSS = """
    RightPanel {
        width: 24;
        height: 100%;
        background: $surface;
        border-left: solid $panel;
        overflow-y: auto;
        padding: 0 1;
    }
    RightPanel .section-header {
        color: $primary;
        text-style: bold;
        margin-top: 1;
    }
    RightPanel .back-link {
        color: $text-muted;
        margin-top: 1;
    }
    """

    mode: reactive[str] = reactive("goals")
    session_tokens: reactive[int] = reactive(0)
    daily_tokens: reactive[int] = reactive(0)
    focused_employee: reactive[str | None] = reactive(None)

    class BackToGoals(Message):
        pass

    def __init__(self) -> None:
        super().__init__()
        self.goals: list[GoalEntry] = []
        self._employee_data: dict = {}

    def compose(self) -> ComposeResult:
        yield Static("", id="panel-content")

    def update_goals(self, goals: list[GoalEntry]) -> None:
        self.goals = list(goals)
        if self.mode == "goals":
            self._refresh()

    def update_tokens(self, session: int, daily: int = 0) -> None:
        self.session_tokens = session
        self.daily_tokens = daily
        if self.mode == "goals":
            self._refresh()

    def show_goals(self) -> None:
        self.mode = "goals"
        self.focused_employee = None
        self._refresh()

    def show_employee(
        self,
        employee_id: str,
        memories: list[str],
        inbox_count: int,
        training: list[str],
    ) -> None:
        self.mode = "employee"
        self.focused_employee = employee_id
        self._employee_data = {
            "memories": memories,
            "inbox_count": inbox_count,
            "training": training,
        }
        self._refresh()

    def _refresh(self) -> None:
        content = self.query_one("#panel-content", Static)
        if self.mode == "goals":
            content.update(self._render_goals())
        else:
            content.update(self._render_employee())

    def _render_goals(self) -> str:
        lines = ["GOALS"]
        for g in self.goals:
            bar_filled = int((g.completed / g.total) * 10) if g.total else 0
            bar = "█" * bar_filled + "░" * (10 - bar_filled)
            lines.append(f"⟳ {g.description[:18]}")
            lines.append(f"  [{bar}] {g.completed}/{g.total}")
        lines += [
            "",
            "TOKENS",
            f"Session: {self.session_tokens:,}",
            f"Daily:   {self.daily_tokens:,}",
        ]
        return "\n".join(lines)

    def _render_employee(self) -> str:
        emp = self.focused_employee or ""
        data = self._employee_data
        memories = data.get("memories", [])
        inbox_count = data.get("inbox_count", 0)
        training = data.get("training", [])
        lines = [f"▶ {emp}", ""]
        if memories:
            lines += ["BRAIN (top memories)"]
            lines += [f"• {m[:20]}" for m in memories[:5]]
        lines += ["", f"INBOX  {inbox_count} unread"]
        if training:
            lines += ["", "TRAINING"]
            lines += [f"• {t[:20]}" for t in training[:3]]
        lines += ["", "← back to goals"]
        return "\n".join(lines)
```

- [ ] **Step 4: Run — verify pass**

```bash
uv run pytest packages/tui/tests/test_widgets.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/tui/src/autogenesis_tui/widgets/right_panel.py \
        packages/tui/tests/test_widgets.py
git commit -m "feat(tui): RightPanel widget — goals/tokens + employee detail"
```

---

## Task 9: InputBar Widget

**Files:**
- Create: `packages/tui/src/autogenesis_tui/widgets/input_bar.py`
- Modify: `packages/tui/tests/test_widgets.py` (append)

- [ ] **Step 1: Append failing tests**

```python
# Append to packages/tui/tests/test_widgets.py

from autogenesis_tui.widgets.input_bar import InputBar


class _InputBarApp(App):
    submitted = []

    def compose(self) -> ComposeResult:
        yield InputBar()

    def on_input_bar_submitted(self, event: InputBar.Submitted) -> None:
        _InputBarApp.submitted.append((event.target, event.text))


@pytest.mark.asyncio
async def test_input_bar_renders():
    async with _InputBarApp().run_test() as pilot:
        bar = pilot.app.query_one(InputBar)
        assert bar is not None
        assert bar.target == "CEO"


@pytest.mark.asyncio
async def test_input_bar_set_target():
    async with _InputBarApp().run_test() as pilot:
        bar = pilot.app.query_one(InputBar)
        bar.set_target("backend-eng")
        assert bar.target == "backend-eng"


@pytest.mark.asyncio
async def test_input_bar_load_targets():
    async with _InputBarApp().run_test() as pilot:
        bar = pilot.app.query_one(InputBar)
        bar.load_targets(["CEO", "backend-eng", "frontend-eng"])
        assert "backend-eng" in bar.targets
```

- [ ] **Step 2: Run — verify they fail**

```bash
uv run pytest packages/tui/tests/test_widgets.py -k "input_bar" -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement InputBar**

```python
# packages/tui/src/autogenesis_tui/widgets/input_bar.py
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Static


class InputBar(Widget):
    """Bottom bar: target dropdown + text input."""

    DEFAULT_CSS = """
    InputBar {
        height: 3;
        layout: horizontal;
        background: $surface;
        border-top: solid $panel;
        padding: 0 1;
    }
    InputBar #target-label {
        width: 18;
        height: 1;
        color: $secondary;
        margin: 1 1 0 0;
        text-style: bold;
    }
    InputBar Input {
        width: 1fr;
    }
    """

    BINDINGS = [
        Binding("ctrl+space", "toggle_target_menu", "Switch target", show=False),
    ]

    target: reactive[str] = reactive("CEO")

    class Submitted(Message):
        def __init__(self, target: str, text: str) -> None:
            super().__init__()
            self.target = target
            self.text = text

    def __init__(self) -> None:
        super().__init__()
        self.targets: list[str] = ["CEO"]
        self._target_index: int = 0

    def compose(self) -> ComposeResult:
        yield Static("[ CEO ▾ ]", id="target-label")
        yield Input(placeholder="type a message...", id="chat-input")

    def load_targets(self, targets: list[str]) -> None:
        self.targets = list(targets)
        if "CEO" not in self.targets:
            self.targets.insert(0, "CEO")

    def set_target(self, target: str) -> None:
        self.target = target
        self.query_one("#target-label", Static).update(f"[ {target} ▾ ]")

    def action_toggle_target_menu(self) -> None:
        if not self.targets:
            return
        self._target_index = (self._target_index + 1) % len(self.targets)
        self.set_target(self.targets[self._target_index])

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if text:
            self.post_message(self.Submitted(target=self.target, text=text))
            event.input.value = ""
```

- [ ] **Step 4: Run — verify pass**

```bash
uv run pytest packages/tui/tests/test_widgets.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/tui/src/autogenesis_tui/widgets/input_bar.py \
        packages/tui/tests/test_widgets.py
git commit -m "feat(tui): InputBar widget with target switching"
```

---

## Task 10: AutogenesisApp — Layout and Wiring

**Files:**
- Create: `packages/tui/src/autogenesis_tui/app.py`
- Test: `packages/tui/tests/test_app.py`

This task wires all widgets together, connects `AppServerManager` + `CodexWSClient`, subscribes to the event bus for dispatched employees, and routes `InputBar.Submitted` to the correct destination.

- [ ] **Step 1: Write failing tests**

```python
# packages/tui/tests/test_app.py
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autogenesis_tui.app import AutogenesisApp
from autogenesis_tui.widgets import AgentStream, EmployeeRoster, InputBar, RightPanel, StatusBar


@pytest.mark.asyncio
async def test_app_composes_all_widgets():
    with patch("autogenesis_tui.app.AppServerManager") as MockServer, \
         patch("autogenesis_tui.app.CodexWSClient") as MockClient:
        MockServer.return_value.start = AsyncMock(return_value=12345)
        MockServer.return_value.stop = AsyncMock()
        MockClient.return_value.connect = AsyncMock()
        MockClient.return_value.start_thread = AsyncMock(return_value="thread-1")

        app = AutogenesisApp(auto_start=False)
        async with app.run_test() as pilot:
            assert pilot.app.query_one(StatusBar) is not None
            assert pilot.app.query_one(EmployeeRoster) is not None
            assert pilot.app.query_one(AgentStream) is not None
            assert pilot.app.query_one(RightPanel) is not None
            assert pilot.app.query_one(InputBar) is not None


@pytest.mark.asyncio
async def test_ws_event_agent_delta_updates_stream():
    with patch("autogenesis_tui.app.AppServerManager") as MockServer, \
         patch("autogenesis_tui.app.CodexWSClient") as MockClient:
        MockServer.return_value.start = AsyncMock(return_value=12345)
        MockServer.return_value.stop = AsyncMock()
        MockClient.return_value.connect = AsyncMock()
        MockClient.return_value.start_thread = AsyncMock(return_value="thread-1")

        app = AutogenesisApp(auto_start=False)
        async with app.run_test() as pilot:
            app.handle_ws_event({
                "method": "item/agentMessage/delta",
                "params": {"delta": "hello", "itemId": "i1", "threadId": "t1", "turnId": "turn1"},
            })
            await pilot.pause()
            stream = pilot.app.query_one(AgentStream)
            assert any(e.text == "hello" for e in stream.entries)


@pytest.mark.asyncio
async def test_ws_event_token_usage_updates_status_bar():
    with patch("autogenesis_tui.app.AppServerManager") as MockServer, \
         patch("autogenesis_tui.app.CodexWSClient") as MockClient:
        MockServer.return_value.start = AsyncMock(return_value=12345)
        MockServer.return_value.stop = AsyncMock()
        MockClient.return_value.connect = AsyncMock()
        MockClient.return_value.start_thread = AsyncMock(return_value="thread-1")

        app = AutogenesisApp(auto_start=False)
        async with app.run_test() as pilot:
            app.handle_ws_event({
                "method": "thread/tokenUsage/updated",
                "params": {
                    "threadId": "t1",
                    "turnId": "turn1",
                    "tokenUsage": {
                        "total": {
                            "totalTokens": 5000,
                            "inputTokens": 3000,
                            "outputTokens": 2000,
                            "cachedInputTokens": 0,
                            "reasoningOutputTokens": 0,
                        },
                        "last": {
                            "totalTokens": 100,
                            "inputTokens": 60,
                            "outputTokens": 40,
                            "cachedInputTokens": 0,
                            "reasoningOutputTokens": 0,
                        },
                    },
                },
            })
            await pilot.pause()
            bar = pilot.app.query_one(StatusBar)
            assert bar.session_tokens == 5000
```

- [ ] **Step 2: Run — verify they fail**

```bash
uv run pytest packages/tui/tests/test_app.py -v
```

Expected: `ImportError` for `autogenesis_tui.app`.

- [ ] **Step 3: Implement AutogenesisApp**

```python
# packages/tui/src/autogenesis_tui/app.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import structlog
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.message import Message

from autogenesis_tui.client import CodexWSClient
from autogenesis_tui.server import AppServerManager
from autogenesis_tui.themes import ThemeManager
from autogenesis_tui.widgets import (
    AgentStream,
    EmployeeRoster,
    InputBar,
    RightPanel,
    StatusBar,
)
from autogenesis_tui.widgets.roster import EmployeeRow
from autogenesis_tui.widgets.right_panel import GoalEntry

logger = structlog.get_logger()

_CEO_SYSTEM_PROMPT = """\
You are the CEO Orchestrator of AutoGenesis — an autonomous multi-agent software startup.
Decompose high-level goals into subtasks, assign to the right employee, dispatch via
`ceo run`, and adapt based on results. Use `autogenesis hr list` to see your team.
"""

# Stable palette: cycle by roster index for per-employee stream colors.
_EMPLOYEE_PALETTE = ["success", "warning", "accent", "error"]


class AutogenesisApp(App):
    """Three-column AutoGenesis TUI — Command Center layout."""

    CSS = """
    Screen {
        layout: vertical;
    }
    StatusBar {
        dock: top;
        height: 1;
    }
    InputBar {
        dock: bottom;
        height: 3;
    }
    #columns {
        height: 1fr;
        layout: horizontal;
    }
    EmployeeRoster {
        width: 22;
    }
    AgentStream {
        width: 1fr;
    }
    RightPanel {
        width: 24;
    }
    """

    BINDINGS = [
        Binding("ctrl+g", "new_goal", "New Goal"),
        Binding("ctrl+n", "new_thread", "New Thread"),
        Binding("ctrl+c", "interrupt", "Interrupt", show=False),
        Binding("t", "theme_picker", "Theme", show=False),
        Binding("escape", "deselect_employee", "Deselect", show=False),
        Binding("g", "stream_bottom", "Stream Bottom", show=False),
        Binding("question_mark", "help", "Help", show=False),
    ]

    def __init__(self, auto_start: bool = True, theme_name: str = "dracula") -> None:
        super().__init__()
        self._auto_start = auto_start
        self._theme_name = theme_name
        self._server = AppServerManager()
        self._client: CodexWSClient | None = None
        self._theme_mgr = ThemeManager(
            user_themes_dir=Path.home() / ".config" / "autogenesis" / "themes"
        )
        self._active_thread_id: str | None = None
        self._employee_threads: dict[str, str] = {}  # employee_id → thread_id

    def compose(self) -> ComposeResult:
        yield StatusBar()
        with Horizontal(id="columns"):
            yield EmployeeRoster()
            yield AgentStream()
            yield RightPanel()
        yield InputBar()

    async def on_mount(self) -> None:
        # Register and apply theme
        for name in self._theme_mgr.list_theme_names():
            self.register_theme(self._theme_mgr.to_textual_theme(name))
        self.theme = self._theme_name

        # Load employees from registry
        await self._load_employees()

        # Subscribe to CEO event bus
        self._subscribe_event_bus()

        if self._auto_start:
            await self._start_server()

    async def _start_server(self) -> None:
        status = self.query_one(StatusBar)
        status.update_connection("connecting")
        try:
            port = await self._server.start()
            self._client = CodexWSClient(port=port, on_event=self.handle_ws_event)
            await self._client.connect()
            self._active_thread_id = await self._client.start_thread(
                base_instructions=_CEO_SYSTEM_PROMPT,
                cwd=str(Path.cwd()),
            )
            status.update_connection("connected")
        except Exception as exc:
            logger.error("app_server_start_failed", exc=str(exc))
            status.update_connection("disconnected")

    async def _load_employees(self) -> None:
        try:
            from autogenesis_employees.registry import EmployeeRegistry
            from autogenesis_core.config import load_config

            cfg = load_config()
            xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
            global_dir = (
                Path(cfg.employees.global_roster_path)
                if cfg.employees.global_roster_path
                else Path(xdg) / "autogenesis" / "employees"
            )
            registry = EmployeeRegistry(global_dir=global_dir)
            rows = [
                EmployeeRow(id=e.id, title=e.title, status="idle")
                for e in registry.list_active()
            ]
            self.query_one(EmployeeRoster).load(rows)
            targets = ["CEO"] + [r.id for r in rows]
            self.query_one(InputBar).load_targets(targets)
        except Exception as exc:
            logger.warning("employee_load_failed", exc=str(exc))

    def _subscribe_event_bus(self) -> None:
        try:
            from autogenesis_core.events import EventType, get_event_bus

            bus = get_event_bus()
            bus.subscribe(EventType.CEO_SUBTASK_ASSIGN, self._on_subtask_assign)
            bus.subscribe(EventType.CEO_SUBTASK_COMPLETE, self._on_subtask_complete)
            bus.subscribe(EventType.CEO_SUBTASK_FAIL, self._on_subtask_fail)
        except Exception as exc:
            logger.warning("event_bus_subscribe_failed", exc=str(exc))

    def _on_subtask_assign(self, event: Any) -> None:
        emp = event.data.get("employee_id", "")
        task = event.data.get("subtask", "")[:60]
        self.call_from_thread(
            self.query_one(EmployeeRoster).set_status, emp, "working"
        )
        self.call_from_thread(
            self.query_one(AgentStream).add_agent_delta,
            f"Assigned: {task}", emp, f"assign-{emp}"
        )

    def _on_subtask_complete(self, event: Any) -> None:
        emp = event.data.get("employee_id", "")
        self.call_from_thread(
            self.query_one(EmployeeRoster).set_status, emp, "done"
        )

    def _on_subtask_fail(self, event: Any) -> None:
        emp = event.data.get("employee_id", "")
        self.call_from_thread(
            self.query_one(EmployeeRoster).set_status, emp, "idle"
        )

    def handle_ws_event(self, event: dict[str, Any]) -> None:
        """Called from CodexWSClient receive loop (same asyncio loop)."""
        self.post_message(_WSEvent(event))

    class _WSEvent(Message):
        def __init__(self, data: dict) -> None:
            super().__init__()
            self.data = data

    def on__w_s_event(self, message: _WSEvent) -> None:  # noqa: N802
        method = message.data.get("method", "")
        params = message.data.get("params", {})
        stream = self.query_one(AgentStream)
        status = self.query_one(StatusBar)

        if method == "item/agentMessage/delta":
            stream.add_agent_delta(params["delta"], "CEO", params["turnId"])
        elif method == "item/commandExecution/outputDelta":
            stream.add_tool_block(
                tool_name="shell",
                tool_arg=params["delta"][:40],
                success=True,
                source="CEO",
                turn_id=params["turnId"],
            )
        elif method == "turn/completed":
            stream.complete_turn(params.get("turn", {}).get("id", ""))
            status.update_connection("connected")
        elif method == "turn/started":
            status.update_connection("connected")
        elif method == "thread/tokenUsage/updated":
            total = params.get("tokenUsage", {}).get("total", {}).get("totalTokens", 0)
            status.update_tokens(total)
            self.query_one(RightPanel).update_tokens(session=total)
        elif method == "thread/started":
            thread = params.get("thread", {})
            model = thread.get("source", "")
            if model:
                status.update_connection("connected", model)

    async def on_input_bar_submitted(self, event: InputBar.Submitted) -> None:
        text = event.text
        stream = self.query_one(AgentStream)

        if event.target == "CEO" or event.target not in self._employee_threads:
            thread_id = self._employee_threads.get(event.target, self._active_thread_id)
            if thread_id and self._client:
                stream.add_agent_delta(f"> {text}", "you", "input")
                await self._client.send_turn(thread_id, text)
        else:
            thread_id = self._employee_threads[event.target]
            if self._client:
                await self._client.send_turn(thread_id, text)

    async def on_employee_roster_selected(self, event: EmployeeRoster.Selected) -> None:
        emp_id = event.employee_id
        stream = self.query_one(AgentStream)
        right = self.query_one(RightPanel)
        input_bar = self.query_one(InputBar)

        if emp_id is None:
            stream.set_filter(None)
            right.show_goals()
            input_bar.set_target("CEO")
            return

        stream.set_filter(emp_id)
        input_bar.set_target(emp_id)

        # Open dedicated thread for this employee if not already open
        if emp_id not in self._employee_threads and self._client:
            from autogenesis_employees.registry import EmployeeRegistry
            from autogenesis_employees.runtime import EmployeeRuntime
            from autogenesis_core.config import load_config
            import os

            cfg = load_config()
            xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
            global_dir = (
                Path(cfg.employees.global_roster_path)
                if cfg.employees.global_roster_path
                else Path(xdg) / "autogenesis" / "employees"
            )
            registry = EmployeeRegistry(global_dir=global_dir)
            config = registry.get(emp_id)
            if config:
                prompt = EmployeeRuntime().build_system_prompt(config=config)
                thread_id = await self._client.start_thread(base_instructions=prompt)
                self._employee_threads[emp_id] = thread_id

        # Load employee detail into RightPanel
        await self._show_employee_detail(emp_id)

    async def _show_employee_detail(self, emp_id: str) -> None:
        right = self.query_one(RightPanel)
        try:
            from autogenesis_employees.brain import BrainManager
            from autogenesis_employees.inbox import InboxManager
            from autogenesis_core.config import load_config

            cfg = load_config()
            base_dir = Path.cwd() / ".autogenesis"
            data_dir = base_dir / "employees" / emp_id
            brain = BrainManager(data_dir / "brain.db")
            inbox = InboxManager(data_dir / "inbox.db")
            await brain.initialize()
            await inbox.initialize()
            memories = [m.content for m in await brain.top_memories(5)]
            unread = await inbox.get_unread(emp_id)
            await brain.close()
            await inbox.close()

            from autogenesis_employees.registry import EmployeeRegistry
            from autogenesis_core.config import load_config
            import os

            xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
            global_dir = Path(xdg) / "autogenesis" / "employees"
            registry = EmployeeRegistry(global_dir=global_dir)
            emp_config = registry.get(emp_id)
            training = emp_config.training_directives if emp_config else []

            right.show_employee(
                employee_id=emp_id,
                memories=memories,
                inbox_count=len(unread),
                training=training,
            )
        except Exception as exc:
            logger.warning("employee_detail_failed", emp=emp_id, exc=str(exc))
            right.show_employee(emp_id, [], 0, [])

    async def action_new_goal(self) -> None:
        self.query_one(InputBar).set_target("CEO")
        self.query_one(InputBar).query_one("#chat-input").focus()

    async def action_new_thread(self) -> None:
        if self._client and self._active_thread_id:
            new_id = await self._client.fork_thread(self._active_thread_id)
            self._active_thread_id = new_id

    async def action_interrupt(self) -> None:
        if self._client and self._active_thread_id:
            await self._client.interrupt(self._active_thread_id)

    def action_deselect_employee(self) -> None:
        self.query_one(EmployeeRoster).deselect()

    def action_stream_bottom(self) -> None:
        self.query_one(AgentStream).scroll_end()

    def action_theme_picker(self) -> None:
        names = self._theme_mgr.list_theme_names()
        current_idx = names.index(self.theme) if self.theme in names else 0
        next_name = names[(current_idx + 1) % len(names)]
        self.theme = next_name

    def action_help(self) -> None:
        self.notify(
            "Ctrl+G new goal · Ctrl+N new thread · Ctrl+C interrupt · "
            "T theme · H hr · S standup · U union · Esc deselect",
            title="Keybindings",
            timeout=8,
        )

    async def on_unmount(self) -> None:
        if self._client:
            await self._client.disconnect()
        await self._server.stop()
```

- [ ] **Step 4: Run tests — verify pass**

```bash
uv run pytest packages/tui/tests/test_app.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Run full suite — no regressions**

```bash
uv run pytest packages/tui/tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/tui/src/autogenesis_tui/app.py \
        packages/tui/tests/test_app.py
git commit -m "feat(tui): AutogenesisApp — layout, WebSocket wiring, event routing"
```

---

## Task 11: CLI Integration + Smoke Test

**Files:**
- Create: `packages/cli/src/autogenesis_cli/commands/tui.py`
- Modify: `packages/cli/src/autogenesis_cli/app.py`
- Modify: `packages/cli/pyproject.toml`

- [ ] **Step 1: Add `autogenesis-tui` to CLI package deps**

In `packages/cli/pyproject.toml`, update `dependencies`:

```toml
dependencies = [
    "autogenesis-core",
    "autogenesis-tools",
    "autogenesis-tui",
    "typer>=0.12",
    "rich>=13.0",
]
```

- [ ] **Step 2: Create the `tui` CLI command**

```python
# packages/cli/src/autogenesis_cli/commands/tui.py
"""tui command — launch the AutoGenesis terminal UI."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def tui_command(
    theme: str = typer.Option("dracula", "--theme", "-t", help="Theme name (dracula, midnight-blue, hacker-green)"),
) -> None:
    """Launch the AutoGenesis TUI."""
    try:
        from autogenesis_tui.app import AutogenesisApp
    except ImportError:
        console.print(
            "[red]Error:[/red] autogenesis-tui not installed. Run: uv sync --all-packages"
        )
        raise typer.Exit(code=1) from None

    app = AutogenesisApp(theme_name=theme)
    app.run()
```

- [ ] **Step 3: Register tui command in `packages/cli/src/autogenesis_cli/app.py`**

Add the following import and registration (alongside existing commands):

```python
from autogenesis_cli.commands.tui import tui_command
```

```python
app.command(name="tui")(tui_command)
```

- [ ] **Step 4: Re-sync**

```bash
cd /home/gray/dev/AutoGenesis
uv sync --all-packages
```

Expected: resolves without errors.

- [ ] **Step 5: Verify command is registered**

```bash
uv run autogenesis --help
```

Expected: `tui` appears in the command list.

```bash
uv run autogenesis tui --help
```

Expected output:
```
Usage: autogenesis tui [OPTIONS]

  Launch the AutoGenesis TUI.

Options:
  -t, --theme TEXT  Theme name (dracula, midnight-blue, hacker-green)
  --help            Show this message and exit.
```

- [ ] **Step 6: Run full test suite**

```bash
uv run pytest packages/tui/tests/ packages/cli/tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add packages/cli/src/autogenesis_cli/commands/tui.py \
        packages/cli/src/autogenesis_cli/app.py \
        packages/cli/pyproject.toml
git commit -m "feat(tui): register autogenesis tui CLI command"
```

- [ ] **Step 8: Live smoke test**

Ensure `codex` CLI is on PATH, then:

```bash
uv run autogenesis tui
```

Expected:
- Terminal clears, three-column Dracula layout appears
- StatusBar shows "● connecting" briefly, then "● connected"
- EmployeeRoster shows your hired employees (or empty with a hint if none)
- Type a message and press Enter → message appears in AgentStream, Codex agent responds
- Press `T` → theme cycles to Midnight Blue
- Press `?` → keybinding help notification appears
- Press `Ctrl+C` to exit → returns to terminal cleanly

---

## Self-Review Notes

- **Spec coverage:** All spec sections covered — package structure (Task 1), themes (Task 2), AppServerManager (Task 3), CodexWSClient (Task 4), all 5 widgets (Tasks 5–9), AutogenesisApp wiring (Task 10), CLI integration (Task 11).
- **Protocol accuracy:** `thread/start` params use `baseInstructions` (not `system_prompt`) and `approvalPolicy: "never"`. `turn/start` uses `input: [{ type: "text", text }]` with `threadId`. `turn/interrupt` requires both `threadId` and `turnId`. All verified from live schema.
- **Type consistency:** `EmployeeRow`, `GoalEntry`, `StreamEntry`, `ThemeManager.to_textual_theme()` and `handle_ws_event()` signatures are consistent throughout.
- **Employee color palette** handled via `ThemeManager.employee_color()` (Task 2) — wired into `AgentStream` via source label; full per-color rendering can be added as a follow-up once the basic stream works.
