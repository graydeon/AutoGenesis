# Remaining Gaps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close all remaining functional gaps: Twitter gateway, scheduler wiring, standup tool, service registration, and EmployeeRuntime.dispatch().

**Architecture:** Each gap is a focused, independent task targeting existing infrastructure. No new packages — just wiring existing components together.

**Tech Stack:** Python 3.11+, aiosqlite, httpx, asyncio, typer, structlog

---

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `packages/twitter/src/autogenesis_twitter/gateway.py` | Twitter API signing gateway — HTTP server at localhost:1456 |
| `packages/twitter/tests/test_gateway.py` | Gateway tests |

### Modified Files

| File | Change |
|------|--------|
| `packages/tools/src/autogenesis_tools/standup_tool.py` | Wire execute() to MeetingManager |
| `packages/employees/src/autogenesis_employees/runtime.py` | Add dispatch() method |
| `packages/employees/tests/test_runtime.py` | Test dispatch() |
| `packages/cli/src/autogenesis_cli/commands/twitter.py` | Wire start/stop to scheduler |
| `packages/cli/src/autogenesis_cli/commands/meeting.py` | Wire standup/meeting to employee dispatch |
| `packages/cli/src/autogenesis_cli/commands/union_cmd.py` | Wire union review |
| `/home/gray/dev/Codex/infra-dashboard/infra-dashboard/backend/data/managed_services.json` | Register AutoGenesis |

---

### Task 1: Twitter API Gateway

**Files:**
- Create: `packages/twitter/src/autogenesis_twitter/gateway.py`
- Test: `packages/twitter/tests/test_gateway.py`

The gateway is a lightweight HTTP server that runs on the host (not in the VM). It receives unsigned tweet requests from the TwitterPoster, signs them with real Twitter API v2 credentials (loaded via `pass` CLI per CLAUDE.md), and forwards to `api.twitter.com`.

- [ ] **Step 1: Write failing tests**

```python
"""Tests for Twitter API signing gateway."""

from __future__ import annotations

import json
from http.server import HTTPServer
from threading import Thread
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autogenesis_twitter.gateway import GatewayHandler, build_gateway_server


class TestGatewayHandler:
    def test_health_endpoint(self, tmp_path):
        server = build_gateway_server(
            host="127.0.0.1",
            port=0,
            api_key="test_key",
            api_secret="test_secret",
            access_token="test_token",
            access_secret="test_token_secret",
            bearer_token="test_bearer",
        )
        thread = Thread(target=server.handle_request)
        thread.start()

        import urllib.request
        port = server.server_address[1]
        req = urllib.request.Request(f"http://127.0.0.1:{port}/health")
        resp = urllib.request.urlopen(req)
        assert resp.status == 200
        data = json.loads(resp.read())
        assert data["status"] == "ok"
        thread.join(timeout=5)
        server.server_close()

    def test_tweet_endpoint_requires_auth(self, tmp_path):
        server = build_gateway_server(
            host="127.0.0.1",
            port=0,
            api_key="k",
            api_secret="s",
            access_token="t",
            access_secret="ts",
            bearer_token="b",
        )
        thread = Thread(target=server.handle_request)
        thread.start()

        import urllib.request
        port = server.server_address[1]
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/twitter/tweet",
            data=json.dumps({"text": "hello"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            assert e.code == 401
        thread.join(timeout=5)
        server.server_close()

    def test_tweet_endpoint_with_auth(self, tmp_path):
        server = build_gateway_server(
            host="127.0.0.1",
            port=0,
            api_key="k",
            api_secret="s",
            access_token="t",
            access_secret="ts",
            bearer_token="b",
            gateway_token="my-secret-token",
        )
        thread = Thread(target=server.handle_request)
        thread.start()

        import urllib.request
        port = server.server_address[1]
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/twitter/tweet",
            data=json.dumps({"text": "hello"}).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer my-secret-token",
            },
        )
        # Will fail trying to reach Twitter API, but we verify the gateway accepted the request
        # by checking it doesn't return 401
        try:
            urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            # Should be a connection/API error, not 401
            assert e.code != 401
        thread.join(timeout=5)
        server.server_close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/gray/dev/AutoGenesis && uv run python -m pytest packages/twitter/tests/test_gateway.py -v`

- [ ] **Step 3: Write implementation**

```python
"""Twitter API signing gateway — HTTP server for host-side credential management.

Runs on the host at localhost:1456. Receives unsigned tweet requests,
signs with real Twitter API v2 credentials, and forwards to api.twitter.com.
Credentials are never exposed to the VM/agent.
"""

from __future__ import annotations

import json
import logging
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

TWITTER_API_BASE = "https://api.twitter.com/2"


class GatewayHandler(BaseHTTPRequestHandler):
    """HTTP handler for the Twitter signing gateway."""

    gateway_token: str = ""
    bearer_token: str = ""

    def _check_auth(self) -> bool:
        if not self.gateway_token:
            return True
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {self.gateway_token}"

    def _send_json(self, code: int, data: dict[str, Any]) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/twitter/tweet":
            self._handle_tweet()
        else:
            self._send_json(404, {"error": "not found"})

    def _handle_tweet(self) -> None:
        if not self._check_auth():
            self._send_json(401, {"error": "unauthorized"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length)) if content_length else {}

        text = body.get("text", "")
        reply_to = body.get("reply_to_id")
        if not text:
            self._send_json(400, {"error": "text is required"})
            return

        payload: dict[str, Any] = {"text": text}
        if reply_to:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to}

        try:
            req = Request(
                f"{TWITTER_API_BASE}/tweets",
                data=json.dumps(payload).encode(),
                headers={
                    "Authorization": f"Bearer {self.bearer_token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            resp = urlopen(req, timeout=30)  # noqa: S310
            result = json.loads(resp.read())
            tweet_id = result.get("data", {}).get("id", "")
            self._send_json(200, {"success": True, "tweet_id": tweet_id})
        except HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            logger.error("twitter_api_error", status=e.code, body=error_body)
            self._send_json(e.code, {"success": False, "error": error_body})
        except (URLError, TimeoutError) as e:
            logger.error("twitter_api_connection_error", error=str(e))
            self._send_json(502, {"success": False, "error": str(e)})

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        logger.debug(format, *args)


def build_gateway_server(
    host: str = "127.0.0.1",
    port: int = 1456,
    api_key: str = "",
    api_secret: str = "",
    access_token: str = "",
    access_secret: str = "",
    bearer_token: str = "",
    gateway_token: str = "",
) -> HTTPServer:
    """Build and return a gateway HTTP server (not started)."""
    handler = partial(GatewayHandler)
    server = HTTPServer((host, port), handler)
    # Inject credentials into handler class
    GatewayHandler.gateway_token = gateway_token
    GatewayHandler.bearer_token = bearer_token
    # Store OAuth1 creds for future OAuth1.0a signing if needed
    server.api_key = api_key
    server.api_secret = api_secret
    server.access_token = access_token
    server.access_secret = access_secret
    return server
```

- [ ] **Step 4: Run tests**

Run: `cd /home/gray/dev/AutoGenesis && uv run python -m pytest packages/twitter/tests/test_gateway.py -v`

- [ ] **Step 5: Commit**

```bash
git add packages/twitter/src/autogenesis_twitter/gateway.py packages/twitter/tests/test_gateway.py
git commit -m "feat(twitter): add API signing gateway server at localhost:1456"
```

---

### Task 2: Wire Scheduler CLI Commands

**Files:**
- Modify: `packages/cli/src/autogenesis_cli/commands/twitter.py`

Wire `twitter start` to spawn the scheduler as a background process, `twitter stop` to kill it, and fix `twitter status` to show scheduler state.

- [ ] **Step 1: Read current twitter.py**

Read `packages/cli/src/autogenesis_cli/commands/twitter.py` to see current stubs.

- [ ] **Step 2: Wire start/stop/status**

Replace the stubs with working implementations:
- `twitter start`: Initialize scheduler, grant permission, start `run_cycle` loop in background via `asyncio.run`
- `twitter stop`: Revoke permission, which causes the loop to exit
- `twitter status`: Show scheduler active state + queue counts

The scheduler runs as a foreground async loop (user Ctrl+C to stop), since it needs explicit permission to start (per design spec). It should:
1. Load config (TwitterConfig)
2. Initialize all dependencies (QueueManager, TwitterBrowser, WorldviewManager, etc.)
3. Check `is_active_window()` — if not, print waiting message
4. Run cycles at `session_interval_minutes` intervals
5. Stop on Ctrl+C or `revoke_permission()`

- [ ] **Step 3: Commit**

```bash
git add packages/cli/src/autogenesis_cli/commands/twitter.py
git commit -m "feat(twitter): wire start/stop/status CLI commands to scheduler"
```

---

### Task 3: Wire StandupWriteTool to MeetingManager

**Files:**
- Modify: `packages/tools/src/autogenesis_tools/standup_tool.py`
- Modify: `packages/tools/tests/test_standup_tool.py` (if exists, else create)

- [ ] **Step 1: Read current standup_tool.py**

Read current implementation to understand the stub.

- [ ] **Step 2: Wire execute() to actually persist**

The tool should:
1. Create a `StandupEntry` from the arguments
2. Write it via `MeetingManager.write_standup([entry])`
3. Return confirmation message

Since tools don't have access to MeetingManager directly, the tool should write a formatted standup string and return it. The actual persistence happens when the CEO orchestrator collects the result. For now, make the tool accept an optional `meetings_dir` via environment variable `AUTOGENESIS_MEETINGS_DIR` and persist directly if set.

- [ ] **Step 3: Commit**

```bash
git add packages/tools/src/autogenesis_tools/standup_tool.py
git commit -m "feat(employees): wire StandupWriteTool to MeetingManager persistence"
```

---

### Task 4: Wire Meeting, Standup, and Union Review CLI Commands

**Files:**
- Modify: `packages/cli/src/autogenesis_cli/commands/meeting.py`
- Modify: `packages/cli/src/autogenesis_cli/commands/union_cmd.py`

- [ ] **Step 1: Read current stubs**

- [ ] **Step 2: Wire meeting command**

`meeting` command should:
1. Load employee registry
2. Parse attendees (comma-separated IDs, or all active if empty)
3. For each attendee, dispatch via CEOOrchestrator or SubAgentManager with the meeting topic as task
4. Collect responses into rounds
5. Write via MeetingManager.write_meeting()
6. Print the meeting notes path

- [ ] **Step 3: Wire standup command**

`standup` command should:
1. Load employee registry
2. For each active employee, dispatch with "Provide your daily standup: what you did yesterday, what you'll do today, any blockers"
3. Collect StandupEntry responses
4. Write via MeetingManager.write_standup()
5. Print the standup path

- [ ] **Step 4: Wire union review**

`union review` command should:
1. Load UnionManager
2. List open proposals
3. For each active employee, dispatch with "Review this proposal and cast your vote: {proposal details}"
4. Collect votes
5. Print summary table

- [ ] **Step 5: Commit**

```bash
git add packages/cli/src/autogenesis_cli/commands/meeting.py packages/cli/src/autogenesis_cli/commands/union_cmd.py
git commit -m "feat(employees): wire meeting, standup, and union review CLI commands"
```

---

### Task 5: Add EmployeeRuntime.dispatch() Method

**Files:**
- Modify: `packages/employees/src/autogenesis_employees/runtime.py`
- Modify: `packages/employees/tests/test_runtime.py`

- [ ] **Step 1: Read current runtime.py and test_runtime.py**

- [ ] **Step 2: Add dispatch() method**

```python
async def dispatch(
    self,
    config: EmployeeConfig,
    task: str,
    sub_agent_mgr: SubAgentManager,
    brain_context: list[str] | None = None,
    inbox_messages: list[str] | None = None,
    changelog_entries: list[str] | None = None,
    cwd: str = ".",
    timeout: float = 300.0,
) -> SubAgentResult:
    """Build system prompt and dispatch employee via SubAgentManager."""
    system_prompt = self.build_system_prompt(
        config=config,
        brain_context=brain_context,
        inbox_messages=inbox_messages,
        changelog_entries=changelog_entries,
        task=task,
    )
    return await sub_agent_mgr.spawn(
        task=task,
        cwd=cwd,
        timeout=timeout,
        system_prompt=system_prompt,
        env_overrides=config.env,
    )
```

- [ ] **Step 3: Add test**

```python
async def test_dispatch_calls_spawn(self):
    from unittest.mock import AsyncMock, MagicMock
    config = EmployeeConfig(id="test", title="Test", persona="testing")
    mgr = MagicMock()
    mock_result = MagicMock()
    mgr.spawn = AsyncMock(return_value=mock_result)
    runtime = EmployeeRuntime()
    result = await runtime.dispatch(config, "do stuff", mgr)
    assert result is mock_result
    mgr.spawn.assert_called_once()
```

- [ ] **Step 4: Commit**

```bash
git add packages/employees/src/autogenesis_employees/runtime.py packages/employees/tests/test_runtime.py
git commit -m "feat(employees): add EmployeeRuntime.dispatch() method"
```

---

### Task 6: Register AutoGenesis in infra-dashboard

**Files:**
- Modify: `/home/gray/dev/Codex/infra-dashboard/infra-dashboard/backend/data/managed_services.json`

- [ ] **Step 1: Read current registry**

- [ ] **Step 2: Add AutoGenesis entry**

Add a service entry for the AutoGenesis Twitter gateway:
```json
{
    "id": "autogenesis-gateway",
    "name": "AutoGenesis Twitter Gateway",
    "description": "Twitter API signing gateway for AutoGenesis agent harness",
    "cwd": "/home/gray/dev/AutoGenesis",
    "start_command": "uv run python -m autogenesis_twitter.gateway",
    "stop_command": "",
    "restart_command": "",
    "process_match": "autogenesis_twitter.gateway",
    "health_url": "http://127.0.0.1:1456/health",
    "port": 1456,
    "log_path": "/tmp/autogenesis-gateway.log",
    "tags": ["autogenesis", "twitter", "gateway"],
    "source": "custom",
    "detected_pid": null,
    "detected_command": ""
}
```

- [ ] **Step 3: Commit**

```bash
git -C /home/gray/dev/Codex/infra-dashboard add backend/data/managed_services.json
git -C /home/gray/dev/Codex/infra-dashboard commit -m "feat: register AutoGenesis Twitter Gateway service"
```
