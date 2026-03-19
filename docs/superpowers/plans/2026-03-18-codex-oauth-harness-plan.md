# Codex OAuth Agent Harness — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform AutoGenesis from a multi-provider LiteLLM wrapper into a focused agent harness powered by OpenAI Codex via OAuth, authenticated through a ChatGPT Plus subscription.

**Architecture:** Replace `ModelRouter` + LiteLLM with a direct `CodexClient` using the OpenAI Responses API over httpx+SSE. Host-side PKCE OAuth flow stores credentials; VM-side `CredentialProvider` ABC reads injected tokens. Sub-agents spawn `codex` CLI as supervised async subprocesses.

**Tech Stack:** Python 3.11+, httpx 0.28.x (async HTTP), httpx-sse 0.4.x (SSE parsing), PyJWT 2.12.x (JWT decoding), Pydantic V2 (data models), Typer + Rich (CLI), structlog (logging), asyncio (async runtime)

**Spec:** `docs/superpowers/specs/2026-03-18-codex-oauth-harness-design.md`

---

## File Structure

### New Files

| File | Responsibility |
|---|---|
| `packages/core/src/autogenesis_core/credentials.py` | `CredentialProvider` ABC + 3 implementations (Gateway, File, Env) |
| `packages/core/src/autogenesis_core/auth.py` | Host-side PKCE OAuth flow, device code flow, token refresh, credential storage |
| `packages/core/src/autogenesis_core/client.py` | `CodexClient` — Responses API + SSE streaming, error handling, retry |
| `packages/core/src/autogenesis_core/responses.py` | `ResponseEventType` enum, `ResponseEvent`, `APIError`, conversation format translation |
| `packages/core/src/autogenesis_core/sub_agents.py` | `SubAgentManager` — supervised Codex CLI subprocess orchestration |
| `packages/core/tests/test_credentials.py` | Tests for all 3 credential providers |
| `packages/core/tests/test_auth.py` | Tests for PKCE generation, token exchange, refresh, storage |
| `packages/core/tests/test_client.py` | Tests for CodexClient (mocked HTTP), SSE parsing, error handling |
| `packages/core/tests/test_responses.py` | Tests for event parsing, conversation format translation |
| `packages/core/tests/test_sub_agents.py` | Tests for SubAgentManager subprocess lifecycle |
| `packages/tools/src/autogenesis_tools/think.py` | `ThinkTool` extracted from `web.py` |
| `packages/cli/src/autogenesis_cli/commands/login.py` | `autogenesis login` command |
| `packages/cli/src/autogenesis_cli/commands/logout.py` | `autogenesis logout` command |
| `packages/cli/src/autogenesis_cli/prompts/default.txt` | Default system instructions for the agent |

### Modified Files

| File | Changes |
|---|---|
| `packages/core/src/autogenesis_core/models.py` | Remove `ModelTier`, `ContentBlock`, `PromptVersion`. Add `ResponseEventType`, keep in `responses.py`. Simplify `TokenUsage` (remove cost fields). |
| `packages/core/src/autogenesis_core/config.py` | Remove `TierConfig`, `ModelConfig` tier references. Add `CodexConfig` (model, api_base_url). Add credential provider config. Simplify `AutoGenesisConfig`. |
| `packages/core/src/autogenesis_core/events.py` | Add auth event types (`AUTH_TOKEN_REFRESH`, `AUTH_LOGIN_SUCCESS`, `AUTH_LOGIN_FAILED`). |
| `packages/core/src/autogenesis_core/loop.py` | Replace `ModelRouter` with `CodexClient`. Pass tool definitions to each API call. Parse Responses API tool calls. Stream text deltas. |
| `packages/core/src/autogenesis_core/context.py` | Update message format for Responses API items. |
| `packages/core/pyproject.toml` | Remove `litellm`. Add `httpx`, `httpx-sse`, `PyJWT`. |
| `packages/tools/src/autogenesis_tools/base.py` | Add `to_responses_api_format()`. Remove `tier_requirement`. |
| `packages/tools/src/autogenesis_tools/registry.py` | Remove tier-based filtering. Keep budget + frequency progressive disclosure. |
| `packages/tools/src/autogenesis_tools/agent.py` | Wire `SubAgentTool` to `SubAgentManager`. Unhide. |
| `packages/tools/src/autogenesis_tools/web.py` | Remove `ThinkTool` (moved to `think.py`). Delete `WebFetchTool`. |
| `packages/tools/pyproject.toml` | Remove `autogenesis-mcp` dependency. |
| `packages/cli/src/autogenesis_cli/app.py` | Register login/logout commands. Remove stub command registrations. Add `--full-auto`, `--model` global flags. |
| `packages/cli/src/autogenesis_cli/display.py` | Rewrite with streaming output, tool approval prompts, Rich formatting. |
| `packages/cli/src/autogenesis_cli/commands/run.py` | Wire to `AgentLoop` + `CodexClient`. Real execution, not echo. |
| `packages/cli/src/autogenesis_cli/commands/chat.py` | Wire to `AgentLoop` + `CodexClient`. Interactive REPL with session state. |
| `packages/cli/pyproject.toml` | Remove deferred package dependencies (optimizer, security, mcp, plugins). |
| `pyproject.toml` (root) | Update dev dependencies. |

### Deleted Files

| File | Reason |
|---|---|
| `packages/core/src/autogenesis_core/router.py` | Replaced by `client.py` |
| `packages/core/src/autogenesis_core/sandbox.py` | VM is the sandbox; no longer needed in core |
| `packages/core/tests/test_router.py` | Replaced by `test_client.py` |
| `packages/core/tests/test_sandbox.py` | No longer needed |
| `packages/tools/src/autogenesis_tools/interactive.py` | `AskUserTool` removed (blocking I/O, headless-incompatible) |
| `packages/tools/src/autogenesis_tools/mcp_tool.py` | MCP deferred |
| `packages/cli/src/autogenesis_cli/commands/optimize.py` | Stub, deferred |
| `packages/cli/src/autogenesis_cli/commands/scan.py` | Stub, deferred |
| `packages/cli/src/autogenesis_cli/commands/audit.py` | Stub, deferred |
| `packages/cli/src/autogenesis_cli/commands/tokens.py` | Stub, deferred |
| `packages/cli/src/autogenesis_cli/commands/plugins.py` | Stub, deferred |
| `packages/cli/src/autogenesis_cli/commands/mcp_cmd.py` | Stub, deferred |
| `packages/cli/src/autogenesis_cli/completions.py` | Not needed for MVP |

---

## Task 1: Update Dependencies

**Files:**
- Modify: `packages/core/pyproject.toml`
- Modify: `packages/tools/pyproject.toml`
- Modify: `packages/cli/pyproject.toml`
- Modify: `pyproject.toml` (root)

- [ ] **Step 1: Update core package dependencies**

In `packages/core/pyproject.toml`, replace `litellm` with the new dependencies:

```toml
[project]
dependencies = [
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "pyyaml>=6.0",
    "structlog>=24.0",
    "httpx>=0.28",
    "httpx-sse>=0.4",
    "PyJWT>=2.8",
]
```

- [ ] **Step 2: Remove MCP dependency from tools**

In `packages/tools/pyproject.toml`, remove `autogenesis-mcp` from dependencies:

```toml
[project]
dependencies = [
    "autogenesis-core",
]
```

- [ ] **Step 3: Slim down CLI dependencies**

In `packages/cli/pyproject.toml`, remove deferred packages:

```toml
[project]
dependencies = [
    "autogenesis-core",
    "autogenesis-tools",
    "typer>=0.12",
    "rich>=13.0",
]
```

- [ ] **Step 4: Sync workspace**

Run: `uv sync --all-extras`
Expected: All dependencies resolve successfully. `litellm` is no longer installed.

- [ ] **Step 5: Commit**

```bash
git add packages/core/pyproject.toml packages/tools/pyproject.toml packages/cli/pyproject.toml pyproject.toml
git commit -m "build: replace litellm with httpx, httpx-sse, PyJWT"
```

---

## Task 2: Core Models Cleanup

**Files:**
- Modify: `packages/core/src/autogenesis_core/models.py`
- Modify: `packages/core/tests/test_models.py`

- [ ] **Step 1: Write tests for the updated models**

In `packages/core/tests/test_models.py`, replace tests for removed types and add tests for simplified models:

```python
"""Tests for core data models."""

from __future__ import annotations

import pytest
from autogenesis_core.models import (
    AgentState,
    Message,
    ToolCall,
    ToolDefinition,
    ToolResult,
    TokenUsage,
)


class TestMessage:
    def test_user_message(self):
        m = Message(role="user", content="hello")
        assert m.role == "user"
        assert m.content == "hello"

    def test_assistant_message_with_tool_calls(self):
        tc = ToolCall(name="bash", arguments={"command": "ls"})
        m = Message(role="assistant", content="", tool_calls=[tc])
        assert len(m.tool_calls) == 1

    def test_tool_call_id_generated(self):
        tc = ToolCall(name="bash", arguments={})
        assert tc.id.startswith("call_")
        assert len(tc.id) == 17  # "call_" + 12 hex chars


class TestToolResult:
    def test_success(self):
        tr = ToolResult(tool_call_id="call_abc", output="done")
        assert tr.output == "done"
        assert tr.is_error is False

    def test_error(self):
        tr = ToolResult(tool_call_id="call_abc", output="fail", is_error=True)
        assert tr.is_error is True


class TestTokenUsage:
    def test_defaults(self):
        t = TokenUsage()
        assert t.input_tokens == 0
        assert t.output_tokens == 0
        assert t.total_tokens == 0

    def test_total_computed(self):
        t = TokenUsage(input_tokens=100, output_tokens=50)
        assert t.total_tokens == 150


class TestAgentState:
    def test_empty_state(self):
        s = AgentState()
        assert s.messages == []
        assert s.metadata == {}

    def test_serialization_roundtrip(self):
        s = AgentState(session_id="test-123")
        data = s.model_dump()
        restored = AgentState.model_validate(data)
        assert restored.session_id == "test-123"


class TestToolDefinition:
    def test_basic(self):
        td = ToolDefinition(
            name="bash",
            description="Run shell commands",
            parameters={"type": "object", "properties": {}},
        )
        assert td.name == "bash"

    def test_no_tier_requirement(self):
        """ModelTier is removed; ToolDefinition has no tier_requirement field."""
        td = ToolDefinition(name="bash", description="test", parameters={})
        assert not hasattr(td, "tier_requirement")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/core/tests/test_models.py -v`
Expected: FAIL — `ModelTier` still exists, `tier_requirement` still on `ToolDefinition`, `TokenUsage` still has cost fields.

- [ ] **Step 3: Rewrite models.py**

Replace `packages/core/src/autogenesis_core/models.py` with:

```python
"""Core data models for AutoGenesis."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A tool invocation requested by the model."""

    id: str = Field(default_factory=lambda: f"call_{uuid4().hex[:12]}")
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    """A conversation message."""

    role: str  # "user", "assistant", "tool"
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_call_id: str | None = None  # for role="tool" messages


class ToolResult(BaseModel):
    """Result from executing a tool."""

    tool_call_id: str
    output: str
    is_error: bool = False


class TokenUsage(BaseModel):
    """Token usage for a single API call."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


class ToolDefinition(BaseModel):
    """Schema for a tool exposed to the model."""

    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    token_cost_estimate: int = 0


class AgentState(BaseModel):
    """Serializable state for an agent session."""

    session_id: str = Field(default_factory=lambda: uuid4().hex[:16])
    messages: list[Message] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/core/tests/test_models.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/autogenesis_core/models.py packages/core/tests/test_models.py
git commit -m "refactor(core): simplify models — remove ModelTier, ContentBlock, PromptVersion"
```

---

## Task 3: Responses API Data Types

**Files:**
- Create: `packages/core/src/autogenesis_core/responses.py`
- Create: `packages/core/tests/test_responses.py`

- [ ] **Step 1: Write tests for response types and conversation translation**

```python
"""Tests for Responses API data types and conversation translation."""

from __future__ import annotations

import json

import pytest
from autogenesis_core.models import Message, ToolCall, ToolResult
from autogenesis_core.responses import (
    APIError,
    ResponseEvent,
    ResponseEventType,
    messages_to_response_input,
    parse_sse_event,
)


class TestResponseEventType:
    def test_text_delta(self):
        assert ResponseEventType.OUTPUT_TEXT_DELTA == "response.output_text.delta"

    def test_function_call_done(self):
        assert ResponseEventType.FUNCTION_CALL_ARGS_DONE == "response.function_call_arguments.done"

    def test_completed(self):
        assert ResponseEventType.COMPLETED == "response.completed"


class TestParseSSEEvent:
    def test_text_delta(self):
        raw = {
            "type": "response.output_text.delta",
            "delta": "Hello",
            "sequence_number": 5,
        }
        event = parse_sse_event("response.output_text.delta", json.dumps(raw))
        assert event.event_type == ResponseEventType.OUTPUT_TEXT_DELTA
        assert event.data["delta"] == "Hello"

    def test_function_call_done(self):
        raw = {
            "type": "response.function_call_arguments.done",
            "name": "bash",
            "arguments": '{"command": "ls"}',
            "call_id": "call_abc123",
        }
        event = parse_sse_event("response.function_call_arguments.done", json.dumps(raw))
        assert event.event_type == ResponseEventType.FUNCTION_CALL_ARGS_DONE
        assert event.data["name"] == "bash"

    def test_unknown_event_type(self):
        raw = {"type": "some.unknown.event"}
        event = parse_sse_event("some.unknown.event", json.dumps(raw))
        assert event.event_type == ResponseEventType.UNKNOWN


class TestMessagesToResponseInput:
    def test_user_message(self):
        messages = [Message(role="user", content="hello")]
        items = messages_to_response_input(messages)
        assert items == [{"role": "user", "content": [{"type": "input_text", "text": "hello"}]}]

    def test_assistant_with_tool_call(self):
        tc = ToolCall(id="call_abc", name="bash", arguments={"command": "ls"})
        messages = [
            Message(role="assistant", content="", tool_calls=[tc]),
        ]
        items = messages_to_response_input(messages)
        assert items[0]["type"] == "function_call"
        assert items[0]["name"] == "bash"
        assert items[0]["call_id"] == "call_abc"

    def test_tool_result(self):
        messages = [
            Message(role="tool", content="output here", tool_call_id="call_abc"),
        ]
        items = messages_to_response_input(messages)
        assert items[0]["type"] == "function_call_output"
        assert items[0]["call_id"] == "call_abc"
        assert items[0]["output"] == "output here"


class TestAPIError:
    def test_from_response(self):
        err = APIError(status_code=429, error_type="rate_limit_error", message="Too many requests")
        assert err.status_code == 429
        assert err.retry_after is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/core/tests/test_responses.py -v`
Expected: FAIL — `autogenesis_core.responses` module does not exist.

- [ ] **Step 3: Implement responses.py**

Create `packages/core/src/autogenesis_core/responses.py`:

```python
"""Responses API data types and conversation format translation."""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from autogenesis_core.models import Message


class ResponseEventType(StrEnum):
    """SSE event types from the OpenAI Responses API."""

    RESPONSE_CREATED = "response.created"
    IN_PROGRESS = "response.in_progress"
    OUTPUT_ITEM_ADDED = "response.output_item.added"
    CONTENT_PART_ADDED = "response.content_part.added"
    OUTPUT_TEXT_DELTA = "response.output_text.delta"
    OUTPUT_TEXT_DONE = "response.output_text.done"
    CONTENT_PART_DONE = "response.content_part.done"
    FUNCTION_CALL_ARGS_DELTA = "response.function_call_arguments.delta"
    FUNCTION_CALL_ARGS_DONE = "response.function_call_arguments.done"
    OUTPUT_ITEM_DONE = "response.output_item.done"
    COMPLETED = "response.completed"
    FAILED = "response.failed"
    RATE_LIMITED = "response.rate_limited"
    UNKNOWN = "unknown"


class ResponseEvent(BaseModel):
    """A parsed SSE event from the Responses API."""

    event_type: ResponseEventType
    data: dict[str, Any] = Field(default_factory=dict)


class APIError(BaseModel):
    """Structured error from the Responses API."""

    status_code: int
    error_type: str
    message: str
    retry_after: float | None = None


class AuthenticationError(Exception):
    """401 from the API — credentials invalid or expired."""


class RateLimitError(Exception):
    """429 from the API — rate limited."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ServerError(Exception):
    """5xx from the API — server-side failure."""


def parse_sse_event(event_type: str, data: str) -> ResponseEvent:
    """Parse a raw SSE event into a ResponseEvent."""
    try:
        parsed_type = ResponseEventType(event_type)
    except ValueError:
        parsed_type = ResponseEventType.UNKNOWN

    try:
        parsed_data = json.loads(data)
    except (json.JSONDecodeError, TypeError):
        parsed_data = {"raw": data}

    return ResponseEvent(event_type=parsed_type, data=parsed_data)


def messages_to_response_input(messages: list[Message]) -> list[dict[str, Any]]:
    """Translate internal Message list to Responses API input items.

    Responses API uses typed items instead of role-based messages:
    - User messages → {"role": "user", "content": [{"type": "input_text", "text": "..."}]}
    - Assistant tool calls → {"type": "function_call", "name": "...", "arguments": "...", "call_id": "..."}
    - Tool results → {"type": "function_call_output", "call_id": "...", "output": "..."}
    """
    items: list[dict[str, Any]] = []

    for msg in messages:
        if msg.role == "user":
            items.append({
                "role": "user",
                "content": [{"type": "input_text", "text": msg.content}],
            })
        elif msg.role == "assistant":
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    items.append({
                        "type": "function_call",
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments),
                        "call_id": tc.id,
                    })
            elif msg.content:
                items.append({
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": msg.content}],
                })
        elif msg.role == "tool":
            items.append({
                "type": "function_call_output",
                "call_id": msg.tool_call_id or "",
                "output": msg.content,
            })

    return items
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/core/tests/test_responses.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/autogenesis_core/responses.py packages/core/tests/test_responses.py
git commit -m "feat(core): add Responses API data types and conversation format translation"
```

---

## Task 4: Credential Provider

**Files:**
- Create: `packages/core/src/autogenesis_core/credentials.py`
- Create: `packages/core/tests/test_credentials.py`

- [ ] **Step 1: Write tests for all three credential providers**

```python
"""Tests for credential providers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from autogenesis_core.credentials import (
    CredentialProvider,
    EnvCredentialProvider,
    FileCredentialProvider,
    GatewayCredentialProvider,
)


class TestCredentialProviderABC:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            CredentialProvider()


class TestEnvCredentialProvider:
    async def test_reads_from_env(self, monkeypatch):
        monkeypatch.setenv("AUTOGENESIS_ACCESS_TOKEN", "tok_123")
        monkeypatch.setenv("AUTOGENESIS_ACCOUNT_ID", "acct_456")
        provider = EnvCredentialProvider()
        assert await provider.get_access_token() == "tok_123"
        assert await provider.get_account_id() == "acct_456"

    async def test_missing_token_raises(self, monkeypatch):
        monkeypatch.delenv("AUTOGENESIS_ACCESS_TOKEN", raising=False)
        provider = EnvCredentialProvider()
        with pytest.raises(RuntimeError, match="AUTOGENESIS_ACCESS_TOKEN"):
            await provider.get_access_token()

    async def test_missing_account_id_raises(self, monkeypatch):
        monkeypatch.delenv("AUTOGENESIS_ACCOUNT_ID", raising=False)
        provider = EnvCredentialProvider()
        with pytest.raises(RuntimeError, match="AUTOGENESIS_ACCOUNT_ID"):
            await provider.get_account_id()


class TestFileCredentialProvider:
    async def test_reads_auth_json(self, tmp_path):
        auth_file = tmp_path / "auth.json"
        auth_file.write_text(json.dumps({
            "access_token": "file_tok",
            "account_id": "file_acct",
            "refresh_token": "refresh_tok",
        }))
        provider = FileCredentialProvider(auth_file)
        assert await provider.get_access_token() == "file_tok"
        assert await provider.get_account_id() == "file_acct"

    async def test_missing_file_raises(self, tmp_path):
        provider = FileCredentialProvider(tmp_path / "missing.json")
        with pytest.raises(FileNotFoundError):
            await provider.get_access_token()

    async def test_reads_fresh_on_each_call(self, tmp_path):
        auth_file = tmp_path / "auth.json"
        auth_file.write_text(json.dumps({"access_token": "v1", "account_id": "acct"}))
        provider = FileCredentialProvider(auth_file)
        assert await provider.get_access_token() == "v1"

        auth_file.write_text(json.dumps({"access_token": "v2", "account_id": "acct"}))
        assert await provider.get_access_token() == "v2"


class TestGatewayCredentialProvider:
    async def test_reads_from_well_known_path(self, tmp_path):
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text(json.dumps({"access_token": "gw_tok", "account_id": "gw_acct"}))
        provider = GatewayCredentialProvider(gateway_path=cred_file)
        assert await provider.get_access_token() == "gw_tok"
        assert await provider.get_account_id() == "gw_acct"

    async def test_missing_gateway_file_raises(self, tmp_path):
        provider = GatewayCredentialProvider(gateway_path=tmp_path / "nope.json")
        with pytest.raises(FileNotFoundError):
            await provider.get_access_token()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/core/tests/test_credentials.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Implement credentials.py**

Create `packages/core/src/autogenesis_core/credentials.py`:

```python
"""Credential providers for accessing OAuth tokens.

The VM-side AutoGenesis never performs OAuth directly. It reads tokens
injected by the host-side gateway via one of these providers.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path


class CredentialProvider(ABC):
    """Abstract base for reading OAuth credentials."""

    @abstractmethod
    async def get_access_token(self) -> str: ...

    @abstractmethod
    async def get_account_id(self) -> str: ...


class EnvCredentialProvider(CredentialProvider):
    """Reads credentials from environment variables.

    Expects AUTOGENESIS_ACCESS_TOKEN and AUTOGENESIS_ACCOUNT_ID.
    """

    async def get_access_token(self) -> str:
        token = os.environ.get("AUTOGENESIS_ACCESS_TOKEN")
        if not token:
            msg = "AUTOGENESIS_ACCESS_TOKEN environment variable not set"
            raise RuntimeError(msg)
        return token

    async def get_account_id(self) -> str:
        account_id = os.environ.get("AUTOGENESIS_ACCOUNT_ID")
        if not account_id:
            msg = "AUTOGENESIS_ACCOUNT_ID environment variable not set"
            raise RuntimeError(msg)
        return account_id


class FileCredentialProvider(CredentialProvider):
    """Reads credentials from an auth.json file.

    For local dev / host-side usage without a VM.
    Reads fresh on every call so external refresh is picked up.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def _read(self) -> dict[str, str]:
        data: dict[str, str] = json.loads(self._path.read_text())
        return data

    async def get_access_token(self) -> str:
        return self._read()["access_token"]

    async def get_account_id(self) -> str:
        return self._read()["account_id"]


_DEFAULT_GATEWAY_PATH = Path("/run/autogenesis/credentials.json")


class GatewayCredentialProvider(CredentialProvider):
    """Reads credentials from a host-mounted file.

    The host-side gateway writes credentials to a well-known path
    and refreshes them atomically. This provider reads fresh on each call.

    Default path: /run/autogenesis/credentials.json
    """

    def __init__(self, gateway_path: Path = _DEFAULT_GATEWAY_PATH) -> None:
        self._path = gateway_path

    def _read(self) -> dict[str, str]:
        data: dict[str, str] = json.loads(self._path.read_text())
        return data

    async def get_access_token(self) -> str:
        return self._read()["access_token"]

    async def get_account_id(self) -> str:
        return self._read()["account_id"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/core/tests/test_credentials.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/autogenesis_core/credentials.py packages/core/tests/test_credentials.py
git commit -m "feat(core): add credential providers (env, file, gateway)"
```

---

## Task 5: Host-Side OAuth Module

**Files:**
- Create: `packages/core/src/autogenesis_core/auth.py`
- Create: `packages/core/tests/test_auth.py`

- [ ] **Step 1: Write tests for PKCE generation and token storage**

```python
"""Tests for host-side OAuth authentication."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import pytest
from autogenesis_core.auth import (
    AuthConfig,
    OAuthCredentials,
    generate_pkce_pair,
    load_credentials,
    save_credentials,
)


class TestPKCE:
    def test_verifier_length(self):
        verifier, challenge = generate_pkce_pair()
        assert 43 <= len(verifier) <= 128

    def test_challenge_is_sha256_of_verifier(self):
        verifier, challenge = generate_pkce_pair()
        expected = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        assert challenge == expected

    def test_no_padding_in_challenge(self):
        _, challenge = generate_pkce_pair()
        assert "=" not in challenge

    def test_unique_each_call(self):
        v1, _ = generate_pkce_pair()
        v2, _ = generate_pkce_pair()
        assert v1 != v2


class TestCredentialStorage:
    def test_save_and_load(self, tmp_path):
        path = tmp_path / "auth.json"
        creds = OAuthCredentials(
            access_token="at_123",
            refresh_token="rt_456",
            id_token="idt_789",
            account_id="acct_abc",
            plan_type="plus",
        )
        save_credentials(creds, path)
        loaded = load_credentials(path)
        assert loaded.access_token == "at_123"
        assert loaded.account_id == "acct_abc"

    def test_file_permissions(self, tmp_path):
        path = tmp_path / "auth.json"
        creds = OAuthCredentials(
            access_token="a", refresh_token="r", id_token="i",
            account_id="acct", plan_type="plus",
        )
        save_credentials(creds, path)
        mode = oct(path.stat().st_mode)[-3:]
        assert mode == "600"

    def test_load_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_credentials(tmp_path / "nope.json")


class TestAuthConfig:
    def test_defaults(self):
        cfg = AuthConfig()
        assert cfg.client_id == "app_EMoamEEZ73f0CkXaXp7hrann"
        assert cfg.auth_base_url == "https://auth.openai.com"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/core/tests/test_auth.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Implement auth.py**

Create `packages/core/src/autogenesis_core/auth.py`:

```python
"""Host-side OAuth PKCE authentication for OpenAI Codex.

This module runs on the HOST machine, not inside the VM.
It handles the browser-based OAuth flow, token exchange,
credential storage, and token refresh.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import stat
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
import jwt
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class OAuthCredentials(BaseModel):
    """Stored OAuth credentials."""

    access_token: str
    refresh_token: str
    id_token: str
    account_id: str
    plan_type: str
    last_refresh: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuthConfig(BaseModel):
    """OAuth configuration."""

    client_id: str = "app_EMoamEEZ73f0CkXaXp7hrann"
    auth_base_url: str = "https://auth.openai.com"
    callback_port: int = 1455
    scopes: list[str] = Field(
        default_factory=lambda: ["openid", "profile", "email", "offline_access"],
    )


def _default_auth_path() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(xdg) / "autogenesis" / "auth.json"


def generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE verifier and S256 challenge."""
    verifier = secrets.token_urlsafe(64)  # 86 chars, within 43-128 range
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def save_credentials(creds: OAuthCredentials, path: Path | None = None) -> None:
    """Save credentials to disk with restrictive permissions."""
    path = path or _default_auth_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(creds.model_dump_json(indent=2))
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0600


def load_credentials(path: Path | None = None) -> OAuthCredentials:
    """Load credentials from disk."""
    path = path or _default_auth_path()
    return OAuthCredentials.model_validate_json(path.read_text())


def _extract_claims(id_token: str) -> dict[str, Any]:
    """Decode JWT id_token to extract claims (no signature verification)."""
    claims: dict[str, Any] = jwt.decode(
        id_token,
        options={"verify_signature": False, "verify_exp": False},
    )
    return claims


class _CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler that captures the OAuth callback."""

    def do_GET(self) -> None:  # noqa: N802
        qs = parse_qs(urlparse(self.path).query)
        server: _CallbackServer = self.server  # type: ignore[assignment]
        server.auth_code = qs.get("code", [None])[0]
        server.auth_state = qs.get("state", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>Login successful. You can close this tab.</h1>")

    def log_message(self, *_args: Any) -> None:
        pass  # suppress HTTP server logs


class _CallbackServer(HTTPServer):
    auth_code: str | None = None
    auth_state: str | None = None


def login(config: AuthConfig | None = None) -> OAuthCredentials:
    """Run the full PKCE OAuth login flow.

    Opens a browser, waits for callback, exchanges code for tokens,
    extracts claims from id_token, and returns credentials.
    """
    config = config or AuthConfig()
    verifier, challenge = generate_pkce_pair()
    state = secrets.token_urlsafe(32)
    redirect_uri = f"http://localhost:{config.callback_port}"

    params = urlencode({
        "client_id": config.client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(config.scopes),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
    })
    auth_url = f"{config.auth_base_url}/authorize?{params}"

    logger.info("opening_browser_for_login", url=auth_url)
    webbrowser.open(auth_url)

    server = _CallbackServer(("127.0.0.1", config.callback_port), _CallbackHandler)
    server.handle_request()

    if not server.auth_code:
        msg = "No authorization code received from callback"
        raise RuntimeError(msg)

    # Exchange code for tokens
    token_response = httpx.post(
        f"{config.auth_base_url}/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": config.client_id,
            "code": server.auth_code,
            "redirect_uri": redirect_uri,
            "code_verifier": verifier,
        },
    )
    token_response.raise_for_status()
    tokens = token_response.json()

    # Extract claims from id_token
    claims = _extract_claims(tokens["id_token"])
    auth_claims = claims.get("https://api.openai.com/auth", {})

    creds = OAuthCredentials(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        id_token=tokens["id_token"],
        account_id=auth_claims.get("chatgpt_account_id", ""),
        plan_type=auth_claims.get("chatgpt_plan_type", "unknown"),
    )

    save_credentials(creds)
    logger.info("login_successful", plan_type=creds.plan_type)
    return creds


def refresh_token(config: AuthConfig | None = None, path: Path | None = None) -> OAuthCredentials:
    """Refresh the access token using the stored refresh token."""
    config = config or AuthConfig()
    creds = load_credentials(path)

    response = httpx.post(
        f"{config.auth_base_url}/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": config.client_id,
            "refresh_token": creds.refresh_token,
        },
    )
    response.raise_for_status()
    tokens = response.json()

    claims = _extract_claims(tokens.get("id_token", creds.id_token))
    auth_claims = claims.get("https://api.openai.com/auth", {})

    updated = OAuthCredentials(
        access_token=tokens["access_token"],
        refresh_token=tokens.get("refresh_token", creds.refresh_token),
        id_token=tokens.get("id_token", creds.id_token),
        account_id=auth_claims.get("chatgpt_account_id", creds.account_id),
        plan_type=auth_claims.get("chatgpt_plan_type", creds.plan_type),
    )

    save_credentials(updated, path)
    logger.info("token_refreshed")
    return updated
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/core/tests/test_auth.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/autogenesis_core/auth.py packages/core/tests/test_auth.py
git commit -m "feat(core): add host-side PKCE OAuth login, token refresh, credential storage"
```

---

## Task 6: CodexClient — Responses API Client

**Files:**
- Create: `packages/core/src/autogenesis_core/client.py`
- Create: `packages/core/tests/test_client.py`

- [ ] **Step 1: Write tests for CodexClient**

```python
"""Tests for CodexClient — Responses API integration."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from autogenesis_core.client import CodexClient, CodexClientConfig
from autogenesis_core.credentials import CredentialProvider
from autogenesis_core.models import Message, ToolDefinition
from autogenesis_core.responses import (
    AuthenticationError,
    RateLimitError,
    ResponseEventType,
    ServerError,
)


class MockCredentialProvider(CredentialProvider):
    async def get_access_token(self) -> str:
        return "test_token"

    async def get_account_id(self) -> str:
        return "test_account"


class TestCodexClientConfig:
    def test_defaults(self):
        cfg = CodexClientConfig()
        assert cfg.model == "gpt-5.3-codex"
        assert cfg.api_base_url == "https://api.openai.com/v1"

    def test_custom_model(self):
        cfg = CodexClientConfig(model="gpt-5.4")
        assert cfg.model == "gpt-5.4"


class TestCodexClientHeaders:
    async def test_builds_correct_headers(self):
        provider = MockCredentialProvider()
        client = CodexClient(credential_provider=provider)
        headers = await client._build_headers()
        assert headers["Authorization"] == "Bearer test_token"
        assert headers["ChatGPT-Account-ID"] == "test_account"
        assert headers["Content-Type"] == "application/json"
        await client.close()


class TestCodexClientRequestBody:
    def test_builds_request(self):
        client = CodexClient(credential_provider=MockCredentialProvider())
        messages = [Message(role="user", content="hello")]
        tools = [ToolDefinition(name="bash", description="Run commands", parameters={})]

        body = client._build_request_body(
            messages=messages,
            instructions="You are a helpful agent.",
            tools=tools,
        )
        assert body["model"] == "gpt-5.3-codex"
        assert body["stream"] is True
        assert body["instructions"] == "You are a helpful agent."
        assert len(body["tools"]) == 1
        assert body["tools"][0]["type"] == "function"
        assert body["tools"][0]["name"] == "bash"


class TestCodexClientErrorHandling:
    async def test_401_raises_auth_error(self):
        provider = MockCredentialProvider()
        client = CodexClient(credential_provider=provider)
        with pytest.raises(AuthenticationError):
            client._handle_http_error(401, {"error": {"message": "Unauthorized"}})
        await client.close()

    async def test_429_raises_rate_limit(self):
        provider = MockCredentialProvider()
        client = CodexClient(credential_provider=provider)
        with pytest.raises(RateLimitError):
            client._handle_http_error(429, {"error": {"message": "Rate limited"}})
        await client.close()

    async def test_500_raises_server_error(self):
        provider = MockCredentialProvider()
        client = CodexClient(credential_provider=provider)
        with pytest.raises(ServerError):
            client._handle_http_error(500, {"error": {"message": "Internal"}})
        await client.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/core/tests/test_client.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Implement client.py**

Create `packages/core/src/autogenesis_core/client.py`:

```python
"""CodexClient — Direct integration with OpenAI Responses API.

Replaces ModelRouter + LiteLLM. Uses httpx for async HTTP
and httpx-sse for SSE stream parsing. Authenticates via
CredentialProvider (OAuth tokens injected by host gateway).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
import structlog
from httpx_sse import aconnect_sse
from pydantic import BaseModel, Field

from autogenesis_core.credentials import CredentialProvider
from autogenesis_core.models import Message, ToolCall, ToolDefinition, TokenUsage
from autogenesis_core.responses import (
    APIError,
    AuthenticationError,
    RateLimitError,
    ResponseEvent,
    ResponseEventType,
    ServerError,
    messages_to_response_input,
    parse_sse_event,
)

logger = structlog.get_logger()


class CodexClientConfig(BaseModel):
    """Configuration for the Codex API client."""

    model: str = "gpt-5.3-codex"
    api_base_url: str = "https://api.openai.com/v1"
    timeout: float = 300.0
    max_retries: int = 3


class CompletionResult(BaseModel):
    """Result from a Responses API call."""

    text: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: TokenUsage = Field(default_factory=TokenUsage)
    response_id: str = ""


class CodexClient:
    """Async client for the OpenAI Responses API."""

    def __init__(
        self,
        credential_provider: CredentialProvider,
        config: CodexClientConfig | None = None,
    ) -> None:
        self._creds = credential_provider
        self._config = config or CodexClientConfig()
        self._http = httpx.AsyncClient(timeout=self._config.timeout)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def _build_headers(self) -> dict[str, str]:
        token = await self._creds.get_access_token()
        account_id = await self._creds.get_account_id()
        return {
            "Authorization": f"Bearer {token}",
            "ChatGPT-Account-ID": account_id,
            "Content-Type": "application/json",
        }

    def _build_request_body(
        self,
        messages: list[Message],
        instructions: str,
        tools: list[ToolDefinition] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self._config.model,
            "instructions": instructions,
            "input": messages_to_response_input(messages),
            "stream": True,
        }
        if tools:
            body["tools"] = [
                {
                    "type": "function",
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                }
                for t in tools
            ]
        return body

    def _handle_http_error(
        self, status_code: int, body: dict[str, Any],
    ) -> None:
        """Raise typed exception based on HTTP status code."""
        error = body.get("error", {})
        message = error.get("message", f"HTTP {status_code}")

        if status_code == 401:  # noqa: PLR2004
            raise AuthenticationError(message)
        if status_code == 429:  # noqa: PLR2004
            raise RateLimitError(message)
        if status_code >= 500:  # noqa: PLR2004
            raise ServerError(message)

    async def create_response(
        self,
        messages: list[Message],
        instructions: str = "",
        tools: list[ToolDefinition] | None = None,
    ) -> AsyncIterator[ResponseEvent]:
        """Stream a response from the Responses API.

        Yields ResponseEvent objects as they arrive via SSE.
        """
        headers = await self._build_headers()
        body = self._build_request_body(messages, instructions, tools)
        url = f"{self._config.api_base_url}/responses"

        async with aconnect_sse(
            self._http, "POST", url, json=body, headers=headers,
        ) as event_source:
            if event_source.response.status_code != 200:  # noqa: PLR2004
                error_body = json.loads(await event_source.response.aread())
                self._handle_http_error(
                    event_source.response.status_code, error_body,
                )

            async for sse in event_source.aiter_sse():
                event = parse_sse_event(sse.event, sse.data)
                yield event

    async def create_response_sync(
        self,
        messages: list[Message],
        instructions: str = "",
        tools: list[ToolDefinition] | None = None,
    ) -> CompletionResult:
        """Non-streaming convenience method. Collects full response."""
        result = CompletionResult()
        text_parts: list[str] = []
        pending_tool_calls: dict[str, dict[str, Any]] = {}

        async for event in self.create_response(messages, instructions, tools):
            if event.event_type == ResponseEventType.OUTPUT_TEXT_DELTA:
                text_parts.append(event.data.get("delta", ""))

            elif event.event_type == ResponseEventType.FUNCTION_CALL_ARGS_DONE:
                call_id = event.data.get("call_id", "")
                name = event.data.get("name", "")
                args_str = event.data.get("arguments", "{}")
                try:
                    args = json.loads(args_str)
                except json.JSONDecodeError:
                    args = {"raw": args_str}
                result.tool_calls.append(
                    ToolCall(id=call_id, name=name, arguments=args),
                )

            elif event.event_type == ResponseEventType.COMPLETED:
                response_data = event.data.get("response", {})
                usage_data = response_data.get("usage", {})
                result.usage = TokenUsage(
                    input_tokens=usage_data.get("input_tokens", 0),
                    output_tokens=usage_data.get("output_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                )
                result.response_id = response_data.get("id", "")

        result.text = "".join(text_parts)
        return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/core/tests/test_client.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/autogenesis_core/client.py packages/core/tests/test_client.py
git commit -m "feat(core): add CodexClient with Responses API streaming via httpx-sse"
```

---

## Task 7: Config Cleanup

**Files:**
- Modify: `packages/core/src/autogenesis_core/config.py`
- Modify: `packages/core/tests/test_config.py`

- [ ] **Step 1: Write tests for simplified config**

Replace `packages/core/tests/test_config.py` with tests that verify:
- `AutoGenesisConfig` has `codex` field (not `models` with tiers)
- `CodexConfig` has `model` and `api_base_url` defaults
- `CredentialProviderType` enum exists (env, file, gateway)
- Config cascade still works (YAML loading, env vars)
- No `TierConfig` or `ModelConfig` references

```python
"""Tests for configuration system."""

from __future__ import annotations

import pytest
from autogenesis_core.config import (
    AutoGenesisConfig,
    CodexConfig,
    CredentialProviderType,
    load_config,
)


class TestCodexConfig:
    def test_defaults(self):
        cfg = CodexConfig()
        assert cfg.model == "gpt-5.3-codex"
        assert cfg.api_base_url == "https://api.openai.com/v1"

    def test_custom_model(self):
        cfg = CodexConfig(model="gpt-5.4")
        assert cfg.model == "gpt-5.4"


class TestAutoGenesisConfig:
    def test_defaults(self):
        cfg = AutoGenesisConfig()
        assert isinstance(cfg.codex, CodexConfig)
        assert cfg.credential_provider == CredentialProviderType.ENV

    def test_serialization_roundtrip(self):
        cfg = AutoGenesisConfig()
        data = cfg.model_dump()
        restored = AutoGenesisConfig.model_validate(data)
        assert restored.codex.model == cfg.codex.model

    def test_no_tier_config(self):
        """TierConfig and ModelConfig are removed."""
        cfg = AutoGenesisConfig()
        assert not hasattr(cfg, "models")


class TestLoadConfig:
    def test_returns_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        monkeypatch.delenv("AUTOGENESIS_CODEX__MODEL", raising=False)
        cfg = load_config()
        assert isinstance(cfg, AutoGenesisConfig)

    def test_env_override(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        monkeypatch.setenv("AUTOGENESIS_CODEX__MODEL", "gpt-5.4")
        cfg = load_config()
        assert cfg.codex.model == "gpt-5.4"
```

- [ ] **Step 2: Run tests, verify they fail, then rewrite config.py**

Rewrite `packages/core/src/autogenesis_core/config.py` replacing `TierConfig`/`ModelConfig` with `CodexConfig` and `CredentialProviderType`. Keep the 6-layer cascade, XDG compliance, YAML loading, env var parsing, and `_deep_merge()`.

- [ ] **Step 3: Run tests to verify they pass**

Run: `uv run pytest packages/core/tests/test_config.py -v`
Expected: All PASS.

- [ ] **Step 4: Commit**

```bash
git add packages/core/src/autogenesis_core/config.py packages/core/tests/test_config.py
git commit -m "refactor(core): simplify config — replace tier routing with CodexConfig"
```

---

## Task 8: Tool Interface Changes

**Files:**
- Modify: `packages/tools/src/autogenesis_tools/base.py`
- Modify: `packages/tools/src/autogenesis_tools/registry.py`
- Create: `packages/tools/src/autogenesis_tools/think.py`
- Modify: `packages/tools/src/autogenesis_tools/web.py` → delete after extracting think
- Delete: `packages/tools/src/autogenesis_tools/interactive.py`
- Delete: `packages/tools/src/autogenesis_tools/mcp_tool.py`
- Modify: `packages/tools/tests/test_registry.py`
- Modify: `packages/tools/tests/test_tools.py`

- [ ] **Step 1: Write test for `to_responses_api_format()`**

Add to `packages/tools/tests/test_tools.py`:

```python
class TestToolResponsesFormat:
    def test_format_structure(self):
        """Tool.to_responses_api_format() returns Responses API tool schema."""
        tool = FakeTool()
        fmt = tool.to_responses_api_format()
        assert fmt["type"] == "function"
        assert fmt["name"] == tool.name
        assert fmt["description"] == tool.description
        assert "parameters" in fmt

    def test_no_tier_requirement(self):
        """tier_requirement property is removed."""
        tool = FakeTool()
        assert not hasattr(tool, "tier_requirement")
```

- [ ] **Step 2: Update base.py — add `to_responses_api_format()`, remove `tier_requirement`**

In `packages/tools/src/autogenesis_tools/base.py`:

```python
def to_responses_api_format(self) -> dict[str, Any]:
    """Convert tool to Responses API function format."""
    return {
        "type": "function",
        "name": self.name,
        "description": self.description,
        "parameters": self.parameters,
    }
```

Remove the `tier_requirement` property entirely.

- [ ] **Step 3: Extract ThinkTool to its own module**

Create `packages/tools/src/autogenesis_tools/think.py` with `ThinkTool` class (copied from `web.py`).

Delete `WebFetchTool` from `web.py`, then delete `web.py` entirely.

- [ ] **Step 4: Delete removed tools**

```bash
rm packages/tools/src/autogenesis_tools/interactive.py
rm packages/tools/src/autogenesis_tools/mcp_tool.py
rm packages/tools/src/autogenesis_tools/web.py
```

- [ ] **Step 5: Update registry.py — remove tier filtering**

In `packages/tools/src/autogenesis_tools/registry.py`, remove the `tier` parameter from `get_definitions_for_context()`. Keep budget and frequency-based progressive disclosure.

- [ ] **Step 6: Update test_registry.py — remove tier test cases**

Remove test classes that test tier-based filtering. Keep budget exhaustion, required tool override, hidden tool filtering, usage frequency sorting tests.

- [ ] **Step 7: Run all tools tests**

Run: `uv run pytest packages/tools/tests/ -v`
Expected: All PASS.

- [ ] **Step 8: Commit**

```bash
git add -A packages/tools/
git commit -m "refactor(tools): add Responses API format, extract think tool, remove deferred tools"
```

---

## Task 9: SubAgentManager

**Files:**
- Create: `packages/core/src/autogenesis_core/sub_agents.py`
- Create: `packages/core/tests/test_sub_agents.py`
- Modify: `packages/tools/src/autogenesis_tools/agent.py`

- [ ] **Step 1: Write tests for SubAgentManager**

```python
"""Tests for SubAgentManager — supervised Codex CLI subprocess orchestration."""

from __future__ import annotations

import asyncio

import pytest
from autogenesis_core.sub_agents import SubAgentManager, SubAgentResult


class TestSubAgentResult:
    def test_success(self):
        r = SubAgentResult(output="done", exit_code=0)
        assert r.success is True

    def test_failure(self):
        r = SubAgentResult(output="error", exit_code=1)
        assert r.success is False


class TestSubAgentManager:
    async def test_spawn_returns_result(self):
        """Spawn a simple echo command as sub-agent."""
        mgr = SubAgentManager(codex_binary="echo")
        result = await mgr.spawn(task="hello world", cwd="/tmp")
        assert result.exit_code == 0
        assert "hello" in result.output.lower() or result.output != ""

    async def test_concurrency_limit(self):
        mgr = SubAgentManager(max_concurrent=1, codex_binary="sleep")
        assert mgr.max_concurrent == 1

    async def test_cancel(self):
        mgr = SubAgentManager(codex_binary="sleep")
        task = asyncio.create_task(mgr.spawn(task="10", cwd="/tmp"))
        await asyncio.sleep(0.1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    async def test_timeout(self):
        mgr = SubAgentManager(codex_binary="sleep")
        result = await mgr.spawn(task="10", cwd="/tmp", timeout=0.5)
        assert result.exit_code != 0 or result.timed_out is True

    async def test_depth_env_var(self):
        """AUTOGENESIS_AGENT_DEPTH is set for child processes."""
        mgr = SubAgentManager(codex_binary="env")
        result = await mgr.spawn(task="", cwd="/tmp")
        assert "AUTOGENESIS_AGENT_DEPTH=1" in result.output
```

- [ ] **Step 2: Run tests to verify they fail, then implement**

Create `packages/core/src/autogenesis_core/sub_agents.py`:

```python
"""SubAgentManager — supervised Codex CLI subprocess orchestration.

Spawns `codex` CLI as async subprocesses for delegated parallel work.
Each sub-agent is monitored and can be cancelled. Depth is enforced
via AUTOGENESIS_AGENT_DEPTH environment variable.
"""

from __future__ import annotations

import asyncio
import os

import structlog
from pydantic import BaseModel, Field

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
        timeout: float = 300.0,
    ) -> SubAgentResult:
        """Spawn a Codex CLI sub-agent and wait for completion."""
        depth = self._get_depth()
        env = {**os.environ, "AUTOGENESIS_AGENT_DEPTH": str(depth + 1)}

        async with self._semaphore:
            logger.info("spawning_sub_agent", task=task[:100], cwd=cwd, depth=depth + 1)

            proc = await asyncio.create_subprocess_exec(
                self._codex_binary,
                "--quiet",
                "--full-auto",
                task,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
            )

            task_id = f"agent_{id(proc)}"
            self._active[task_id] = proc

            try:
                stdout, _ = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout,
                )
                output = stdout.decode("utf-8", errors="replace")
                if len(output) > _MAX_OUTPUT_CHARS:
                    output = output[:_MAX_OUTPUT_CHARS] + f"\n[truncated — {len(output)} chars total]"

                return SubAgentResult(
                    output=output,
                    exit_code=proc.returncode or 0,
                )
            except asyncio.TimeoutError:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    proc.kill()
                return SubAgentResult(output="Sub-agent timed out", exit_code=-1, timed_out=True)
            finally:
                self._active.pop(task_id, None)

    async def cancel_all(self) -> None:
        """Terminate all active sub-agents."""
        for task_id, proc in list(self._active.items()):
            proc.terminate()
            logger.info("cancelled_sub_agent", task_id=task_id)
        self._active.clear()
```

- [ ] **Step 3: Wire SubAgentTool to SubAgentManager**

Update `packages/tools/src/autogenesis_tools/agent.py`:

```python
"""Sub-agent tool — delegates tasks to Codex CLI subprocesses."""

from __future__ import annotations

from typing import Any

from autogenesis_tools.base import Tool


class SubAgentTool(Tool):
    """Delegate a task to a Codex CLI sub-agent."""

    def __init__(self, sub_agent_manager: Any = None) -> None:
        self._manager = sub_agent_manager

    @property
    def name(self) -> str:
        return "sub_agent"

    @property
    def description(self) -> str:
        return (
            "Delegate a task to a Codex CLI sub-agent. The sub-agent runs in its own "
            "process with full autonomy. Use for independent subtasks that can run in parallel."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Task description for the sub-agent"},
                "cwd": {"type": "string", "description": "Working directory for the sub-agent"},
            },
            "required": ["task"],
        }

    @property
    def hidden(self) -> bool:
        return False

    @property
    def token_cost_estimate(self) -> int:
        return 200

    async def execute(self, arguments: dict[str, Any]) -> str:
        if self._manager is None:
            return "Error: SubAgentManager not configured"

        result = await self._manager.spawn(
            task=arguments["task"],
            cwd=arguments.get("cwd", "."),
        )

        if result.success:
            return f"Sub-agent completed successfully:\n{result.output}"
        if result.timed_out:
            return "Sub-agent timed out"
        return f"Sub-agent failed (exit code {result.exit_code}):\n{result.output}"
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest packages/core/tests/test_sub_agents.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/autogenesis_core/sub_agents.py packages/core/tests/test_sub_agents.py packages/tools/src/autogenesis_tools/agent.py
git commit -m "feat(core): add SubAgentManager for supervised Codex CLI sub-agents"
```

---

## Task 10: Agent Loop Refactor

**Files:**
- Modify: `packages/core/src/autogenesis_core/loop.py`
- Modify: `packages/core/tests/test_loop.py`
- Delete: `packages/core/src/autogenesis_core/router.py`
- Delete: `packages/core/src/autogenesis_core/sandbox.py`
- Delete: `packages/core/tests/test_router.py`
- Delete: `packages/core/tests/test_sandbox.py`

- [ ] **Step 1: Write tests for the refactored agent loop**

Rewrite `packages/core/tests/test_loop.py` to test against `CodexClient` instead of `ModelRouter`. Mock the `create_response()` method to yield fake SSE events. Test:

- Loop runs and collects text output
- Loop handles tool calls (function_call_arguments.done event → execute tool → feed result back)
- Loop respects max_iterations
- Loop handles cancellation
- Loop saves state after each iteration
- Loop passes tool definitions to each API call

- [ ] **Step 2: Rewrite loop.py**

Replace `ModelRouter` with `CodexClient`. The loop:

1. Calls `client.create_response(messages, instructions, tool_defs)`
2. Iterates over yielded `ResponseEvent` objects
3. On text delta: accumulates text, streams to display callback
4. On function_call_arguments.done: creates `ToolCall`, executes via tool executor, appends result to messages
5. On completed: extracts usage, breaks
6. If tool calls were made, loops back to step 1 with updated messages
7. Persists state after each iteration

- [ ] **Step 3: Delete removed files**

```bash
rm packages/core/src/autogenesis_core/router.py
rm packages/core/src/autogenesis_core/sandbox.py
rm packages/core/tests/test_router.py
rm packages/core/tests/test_sandbox.py
```

- [ ] **Step 4: Run all core tests**

Run: `uv run pytest packages/core/tests/ -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add -A packages/core/
git commit -m "refactor(core): rewire agent loop to CodexClient, remove ModelRouter"
```

---

## Task 11: CLI Display Layer

**Files:**
- Modify: `packages/cli/src/autogenesis_cli/display.py`
- Create: `packages/cli/src/autogenesis_cli/prompts/default.txt`

- [ ] **Step 1: Write the default system instructions**

Create `packages/cli/src/autogenesis_cli/prompts/default.txt`:

```
You are AutoGenesis, an autonomous coding agent. You have access to tools for reading, writing, and editing files, running shell commands, searching code, and delegating tasks to sub-agents.

When given a task:
1. Understand the request fully before acting
2. Use tools to explore the codebase and gather context
3. Make changes incrementally, verifying each step
4. Use the think tool to reason through complex decisions
5. Delegate independent subtasks to sub-agents when beneficial

Work autonomously. Be thorough but efficient. Prefer small, focused changes over large rewrites.
```

- [ ] **Step 2: Rewrite display.py with streaming, tool approval, Rich formatting**

Rewrite `packages/cli/src/autogenesis_cli/display.py`:

```python
"""Rich-based display layer for AutoGenesis CLI.

Handles streaming text output, tool call display with approval prompts,
and error/warning formatting. Headless-compatible (no TUI framework).
"""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

console = Console()

# Tools that are auto-approved by default (read-only operations)
_AUTO_APPROVED_TOOLS: set[str] = {"file_read", "glob", "grep", "list_dir", "think"}


class ApprovalManager:
    """Manages tool execution approval state for a session."""

    def __init__(self, full_auto: bool = False) -> None:
        self._full_auto = full_auto
        self._session_approved: set[str] = set()

    def should_prompt(self, tool_name: str) -> bool:
        if self._full_auto:
            return False
        if tool_name in _AUTO_APPROVED_TOOLS:
            return False
        return tool_name not in self._session_approved

    def prompt_user(self, tool_name: str, arguments: dict[str, Any]) -> bool:
        args_preview = _format_args_preview(tool_name, arguments)
        console.print(f"\n[yellow][Allow][/yellow] {tool_name}: {args_preview}")
        response = console.input("[y/n/always] ").strip().lower()
        if response == "always":
            self._session_approved.add(tool_name)
            return True
        return response in ("y", "yes")


def print_text_delta(delta: str) -> None:
    """Print a streaming text delta (no newline)."""
    console.print(delta, end="", highlight=False)


def print_text_done() -> None:
    """Print a newline after streaming text is complete."""
    console.print()


def print_tool_call(tool_name: str, arguments: dict[str, Any]) -> None:
    """Display a tool call being executed."""
    args_preview = _format_args_preview(tool_name, arguments)
    console.print(f"\n[dim]> {tool_name}:[/dim] {args_preview}")


def print_tool_result(tool_name: str, output: str, is_error: bool = False) -> None:
    """Display a tool execution result."""
    style = "red" if is_error else "green"
    truncated = output[:2000] + "..." if len(output) > 2000 else output
    console.print(Panel(truncated, title=f"{tool_name} result", border_style=style, expand=False))


def print_error(message: str) -> None:
    """Display an error message."""
    console.print(f"[red]Error:[/red] {message}")


def print_warning(message: str) -> None:
    """Display a warning message."""
    console.print(f"[yellow]Warning:[/yellow] {message}")


def print_info(message: str) -> None:
    """Display an info message."""
    console.print(f"[blue]{message}[/blue]")


def _format_args_preview(tool_name: str, arguments: dict[str, Any]) -> str:
    """Format tool arguments for display."""
    if tool_name == "bash":
        return str(arguments.get("command", ""))
    if tool_name in ("file_read", "file_write", "file_edit"):
        return str(arguments.get("path", ""))
    if tool_name == "sub_agent":
        return str(arguments.get("task", ""))[:100]
    return str(arguments)[:200]
```

- [ ] **Step 3: Commit**

```bash
git add packages/cli/src/autogenesis_cli/display.py packages/cli/src/autogenesis_cli/prompts/
git commit -m "feat(cli): add Rich streaming display layer with tool approval prompts"
```

---

## Task 12: CLI Commands — Login, Logout, Run, Chat

**Files:**
- Create: `packages/cli/src/autogenesis_cli/commands/login.py`
- Create: `packages/cli/src/autogenesis_cli/commands/logout.py`
- Modify: `packages/cli/src/autogenesis_cli/commands/run.py`
- Modify: `packages/cli/src/autogenesis_cli/commands/chat.py`
- Modify: `packages/cli/src/autogenesis_cli/app.py`
- Delete: `packages/cli/src/autogenesis_cli/commands/optimize.py`
- Delete: `packages/cli/src/autogenesis_cli/commands/scan.py`
- Delete: `packages/cli/src/autogenesis_cli/commands/audit.py`
- Delete: `packages/cli/src/autogenesis_cli/commands/tokens.py`
- Delete: `packages/cli/src/autogenesis_cli/commands/plugins.py`
- Delete: `packages/cli/src/autogenesis_cli/commands/mcp_cmd.py`
- Delete: `packages/cli/src/autogenesis_cli/completions.py`

- [ ] **Step 1: Create login command**

`packages/cli/src/autogenesis_cli/commands/login.py`:

```python
"""Login command — host-side PKCE OAuth flow."""

from __future__ import annotations

import typer
from rich.console import Console

from autogenesis_core.auth import AuthConfig, load_credentials, login

console = Console()


def login_command(
    device_code: bool = typer.Option(False, "--device-code", help="Use device code flow for headless hosts"),
) -> None:
    """Authenticate with OpenAI via OAuth (ChatGPT Plus subscription)."""
    try:
        existing = load_credentials()
        console.print(f"[yellow]Already authenticated (plan: {existing.plan_type})[/yellow]")
        console.print("Run [bold]autogenesis logout[/bold] first to re-authenticate.")
        raise typer.Exit
    except FileNotFoundError:
        pass

    if device_code:
        console.print("[yellow]Device code flow is a stretch goal — not yet implemented.[/yellow]")
        raise typer.Exit(code=1)

    console.print("[blue]Opening browser for OpenAI login...[/blue]")
    creds = login()
    console.print(f"[green]Authenticated![/green] Plan: {creds.plan_type}")
```

- [ ] **Step 2: Create logout command**

`packages/cli/src/autogenesis_cli/commands/logout.py`:

```python
"""Logout command — wipe stored credentials."""

from __future__ import annotations

import typer
from rich.console import Console

from autogenesis_core.auth import _default_auth_path

console = Console()


def logout_command() -> None:
    """Remove stored OAuth credentials."""
    path = _default_auth_path()
    if path.exists():
        path.unlink()
        console.print("[green]Logged out successfully.[/green]")
    else:
        console.print("[yellow]Not authenticated — nothing to do.[/yellow]")
```

- [ ] **Step 3: Rewrite run command — wire to AgentLoop + CodexClient**

`packages/cli/src/autogenesis_cli/commands/run.py`:

```python
"""Run command — single-shot task execution."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console

from autogenesis_cli.display import ApprovalManager, print_error

console = Console()

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def run_command(
    prompt: str = typer.Argument("", help="Task to execute"),
    full_auto: bool = typer.Option(False, "--full-auto", help="Bypass all approval prompts"),
    model: str = typer.Option("gpt-5.3-codex", "--model", help="Model to use"),
    quiet: bool = typer.Option(False, "--quiet", help="Minimal output"),
) -> None:
    """Execute a single task and exit."""
    if not prompt:
        if not sys.stdin.isatty():
            prompt = sys.stdin.read().strip()
        if not prompt:
            print_error("No prompt provided. Usage: autogenesis run 'your task'")
            raise typer.Exit(code=1)

    asyncio.run(_run_async(prompt, full_auto, model, quiet))


async def _run_async(prompt: str, full_auto: bool, model: str, quiet: bool) -> None:
    from autogenesis_core.client import CodexClient, CodexClientConfig
    from autogenesis_core.config import load_config
    from autogenesis_core.credentials import EnvCredentialProvider
    from autogenesis_core.loop import AgentLoop
    from autogenesis_tools.registry import ToolRegistry

    config = load_config()
    provider = EnvCredentialProvider()
    client_config = CodexClientConfig(model=model)
    client = CodexClient(credential_provider=provider, config=client_config)

    registry = ToolRegistry()
    # Register tools (lazy import to avoid circular deps)
    from autogenesis_tools.bash import BashTool
    from autogenesis_tools.filesystem import (
        FileEditTool,
        FileReadTool,
        FileWriteTool,
        GlobTool,
        GrepTool,
        ListDirTool,
    )
    from autogenesis_tools.think import ThinkTool

    for tool_cls in [BashTool, FileReadTool, FileWriteTool, FileEditTool,
                     GlobTool, GrepTool, ListDirTool, ThinkTool]:
        registry.register(tool_cls())

    instructions = (_PROMPTS_DIR / "default.txt").read_text()
    approval = ApprovalManager(full_auto=full_auto)

    loop = AgentLoop(
        client=client,
        tool_registry=registry,
        instructions=instructions,
        approval_manager=approval,
    )

    try:
        result = await loop.run(prompt)
        if not quiet:
            console.print(f"\n[dim]Tokens: {result.usage.total_tokens}[/dim]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
    finally:
        await client.close()
```

- [ ] **Step 4: Rewrite chat command — interactive REPL**

`packages/cli/src/autogenesis_cli/commands/chat.py` — similar to run but in a loop, reading user input with `console.input()`, maintaining conversation state across turns, supporting `--resume`.

- [ ] **Step 5: Rewrite app.py — register new commands, add global flags**

```python
"""AutoGenesis CLI application."""

from __future__ import annotations

from importlib.metadata import version

import typer

app = typer.Typer(
    name="autogenesis",
    help="The token-efficient agent harness powered by OpenAI Codex.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        v = version("autogenesis-cli")
        typer.echo(f"autogenesis {v}")
        raise typer.Exit


@app.callback()
def main_callback(
    _version: bool = typer.Option(
        False, "--version", "-V", callback=_version_callback,
        is_eager=True, help="Show version and exit.",
    ),
) -> None:
    """AutoGenesis — autonomous agent harness."""


# Register commands
from autogenesis_cli.commands.login import login_command
from autogenesis_cli.commands.logout import logout_command
from autogenesis_cli.commands.run import run_command
from autogenesis_cli.commands.chat import chat_command
from autogenesis_cli.commands.config import config as config_command

app.command(name="login")(login_command)
app.command(name="logout")(logout_command)
app.command(name="run")(run_command)
app.command(name="chat")(chat_command)
app.command(name="config")(config_command)


def main() -> None:
    app()
```

- [ ] **Step 6: Delete stub commands**

```bash
rm packages/cli/src/autogenesis_cli/commands/optimize.py
rm packages/cli/src/autogenesis_cli/commands/scan.py
rm packages/cli/src/autogenesis_cli/commands/audit.py
rm packages/cli/src/autogenesis_cli/commands/tokens.py
rm packages/cli/src/autogenesis_cli/commands/plugins.py
rm packages/cli/src/autogenesis_cli/commands/mcp_cmd.py
rm packages/cli/src/autogenesis_cli/completions.py
```

- [ ] **Step 7: Run CLI tests**

Run: `uv run pytest packages/cli/tests/ -v`
Expected: All PASS (tests may need updating for new command signatures).

- [ ] **Step 8: Commit**

```bash
git add -A packages/cli/
git commit -m "feat(cli): implement login/logout/run/chat commands with Codex integration"
```

---

## Task 13: Update Events and Context

**Files:**
- Modify: `packages/core/src/autogenesis_core/events.py`
- Modify: `packages/core/src/autogenesis_core/context.py`

- [ ] **Step 1: Add auth event types to events.py**

Add to `EventType` enum:
```python
AUTH_TOKEN_REFRESH = "auth.token.refresh"
AUTH_LOGIN_SUCCESS = "auth.login.success"
AUTH_LOGIN_FAILED = "auth.login.failed"
```

- [ ] **Step 2: Update context.py for Responses API format**

The `ContextManager` estimates tokens for messages. Update the token estimation to work with the Responses API item format. The internal `Message` model doesn't change, so this is minimal — just ensure the char-based estimation still works.

- [ ] **Step 3: Run tests**

Run: `uv run pytest packages/core/tests/test_events.py packages/core/tests/test_context.py -v`
Expected: All PASS.

- [ ] **Step 4: Commit**

```bash
git add packages/core/src/autogenesis_core/events.py packages/core/src/autogenesis_core/context.py
git commit -m "feat(core): add auth events, update context for Responses API"
```

---

## Task 14: Fix Cross-Package Tests and Lint

**Files:**
- Modify: various test files and source files as needed

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest packages/core/tests/ packages/tools/tests/ packages/cli/tests/ -v`
Expected: All PASS.

- [ ] **Step 2: Run ruff lint**

Run: `uv run ruff check packages/core/ packages/tools/ packages/cli/`
Fix any lint errors.

- [ ] **Step 3: Run ruff format**

Run: `uv run ruff format packages/core/ packages/tools/ packages/cli/`

- [ ] **Step 4: Run mypy**

Run: `uv run mypy packages/core/ packages/tools/ packages/cli/`
Fix type errors. Common issues: removed imports of `ModelTier`, `litellm`, etc.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "fix: resolve lint, format, and type check issues across all MVP packages"
```

---

## Task 15: Update Deferred Packages for Compatibility

The deferred packages (tokens, security, optimizer, mcp, plugins) may have import errors since `ModelTier`, `litellm`, etc. are removed. They don't need new features, but they need to not break the workspace.

**Files:**
- Modify: `packages/tokens/src/autogenesis_tokens/counter.py` (remove litellm imports)
- Modify: various test files if they reference removed types

- [ ] **Step 1: Fix counter.py**

Replace litellm calls with stub implementations that raise `NotImplementedError("Token counting not yet ported to Codex — deferred to post-MVP")`.

- [ ] **Step 2: Fix any broken imports across deferred packages**

Search for references to `ModelTier`, `ContentBlock`, `PromptVersion`, `TierConfig`, `ModelConfig` in all packages and update/remove them.

- [ ] **Step 3: Run full workspace tests**

Run: `uv run pytest packages/*/tests/ -v --tb=short`
Expected: All PASS (deferred package tests may need adjustment).

- [ ] **Step 4: Run full lint + type check**

Run: `uv run ruff check packages/ && uv run ruff format --check packages/ && uv run mypy packages/`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "fix: update deferred packages for compatibility with simplified core models"
```

---

## Task 16: Integration Smoke Test

- [ ] **Step 1: Manual smoke test (no real API call)**

Set up environment with mock credentials:
```bash
export AUTOGENESIS_ACCESS_TOKEN="test_token"
export AUTOGENESIS_ACCOUNT_ID="test_account"
```

Run: `autogenesis --version`
Expected: Version string printed.

Run: `autogenesis config show`
Expected: Config displayed with `codex.model = gpt-5.3-codex`.

Run: `autogenesis run "hello" --quiet`
Expected: Connection error (expected — no real API). Verify it attempts to connect to `api.openai.com/v1/responses`, not LiteLLM.

- [ ] **Step 2: Push to GitHub**

```bash
git push origin main
```

Expected: CI runs. Some jobs may fail (deferred packages), but core/tools/cli should build and test successfully.

- [ ] **Step 3: Commit any fixes from smoke testing**

```bash
git add -A
git commit -m "fix: address issues found during integration smoke test"
```

---

## Addendum: Review Fixes

The following items address gaps identified during plan review. Implementers should apply these alongside the tasks they reference.

### A1: Task Dependencies (Apply to all tasks)

| Task | Depends On |
|---|---|
| Task 7 (Config Cleanup) | Task 2 (Models) |
| Task 8 (Tool Interface) | Task 2 (Models) |
| Task 9 (SubAgentManager) | Task 3 (Responses) |
| Task 10 (Agent Loop) | Tasks 2, 3, 4, 6, 8 |
| Task 11 (Display) | None |
| Task 12 (CLI Commands) | Tasks 5, 6, 8, 9, 10, 11 |

### A2: Task 7 — Full Config Implementation (Critical Fix)

Replace the prose "rewrite config.py" step with this complete implementation:

```python
"""Configuration system for AutoGenesis.

6-layer cascade: defaults → system → user → project → env → CLI flags.
XDG Base Directory compliant.
"""

from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path
from typing import Any

import structlog
import yaml
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class CredentialProviderType(StrEnum):
    """How AutoGenesis obtains OAuth credentials."""

    ENV = "env"
    FILE = "file"
    GATEWAY = "gateway"


class CodexConfig(BaseModel):
    """OpenAI Codex API configuration."""

    model: str = "gpt-5.3-codex"
    api_base_url: str = "https://api.openai.com/v1"
    timeout: float = 300.0
    max_retries: int = 3


class TokenConfig(BaseModel):
    """Token budget limits (token counts, not USD — subscription billing)."""

    max_tokens_per_session: int = 500_000
    max_tokens_per_day: int = 5_000_000


class SecurityConfig(BaseModel):
    """Security settings."""

    guardrails_enabled: bool = True


class AutoGenesisConfig(BaseModel):
    """Root configuration model."""

    codex: CodexConfig = Field(default_factory=CodexConfig)
    tokens: TokenConfig = Field(default_factory=TokenConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    credential_provider: CredentialProviderType = CredentialProviderType.ENV
    credential_path: str = ""  # for file/gateway providers


def _xdg_config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))


def _find_project_config() -> Path | None:
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / ".autogenesis" / "config.yaml"
        if candidate.exists():
            return candidate
    return None


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open() as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        logger.warning("config_load_failed", path=str(path))
        return {}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _env_overrides() -> dict[str, Any]:
    """Parse AUTOGENESIS_* env vars into nested dict. Uses __ as separator."""
    prefix = "AUTOGENESIS_"
    result: dict[str, Any] = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        parts = key[len(prefix):].lower().split("__")
        current = result
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value
    return result


def load_config() -> AutoGenesisConfig:
    """Load configuration with 6-layer cascade."""
    merged: dict[str, Any] = {}

    # Layer 2: System config
    merged = _deep_merge(merged, _load_yaml(Path("/etc/autogenesis/config.yaml")))

    # Layer 3: User config
    merged = _deep_merge(merged, _load_yaml(_xdg_config_home() / "autogenesis" / "config.yaml"))

    # Layer 4: Project config
    project = _find_project_config()
    if project:
        merged = _deep_merge(merged, _load_yaml(project))

    # Layer 5: Environment variables
    merged = _deep_merge(merged, _env_overrides())

    return AutoGenesisConfig.model_validate(merged)
```

### A3: Task 10 — Full Agent Loop Implementation (Critical Fix)

Replace the prose steps with this complete implementation:

**Test file** (`packages/core/tests/test_loop.py`):

```python
"""Tests for the refactored agent loop."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from autogenesis_core.client import CodexClient, CompletionResult
from autogenesis_core.credentials import CredentialProvider
from autogenesis_core.loop import AgentLoop, AgentLoopResult
from autogenesis_core.models import Message, ToolCall, TokenUsage
from autogenesis_core.responses import ResponseEvent, ResponseEventType


class MockCredentialProvider(CredentialProvider):
    async def get_access_token(self) -> str:
        return "test"

    async def get_account_id(self) -> str:
        return "test"


def _make_text_events(text: str) -> list[ResponseEvent]:
    return [
        ResponseEvent(
            event_type=ResponseEventType.OUTPUT_TEXT_DELTA,
            data={"delta": text},
        ),
        ResponseEvent(
            event_type=ResponseEventType.COMPLETED,
            data={"response": {"id": "resp_1", "usage": {
                "input_tokens": 10, "output_tokens": 5, "total_tokens": 15,
            }}},
        ),
    ]


def _make_tool_call_events(name: str, arguments: dict) -> list[ResponseEvent]:
    return [
        ResponseEvent(
            event_type=ResponseEventType.FUNCTION_CALL_ARGS_DONE,
            data={"name": name, "arguments": json.dumps(arguments), "call_id": "call_123"},
        ),
        ResponseEvent(
            event_type=ResponseEventType.COMPLETED,
            data={"response": {"id": "resp_1", "usage": {
                "input_tokens": 10, "output_tokens": 5, "total_tokens": 15,
            }}},
        ),
    ]


class TestAgentLoop:
    async def test_simple_text_response(self):
        client = MagicMock(spec=CodexClient)

        async def fake_stream(*args, **kwargs):
            for event in _make_text_events("Hello world"):
                yield event

        client.create_response = MagicMock(return_value=fake_stream())

        loop = AgentLoop(client=client)
        result = await loop.run("say hello")
        assert result.output == "Hello world"
        assert result.usage.total_tokens == 15

    async def test_tool_call_and_response(self):
        client = MagicMock(spec=CodexClient)
        call_count = 0

        async def fake_stream(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                for event in _make_tool_call_events("bash", {"command": "echo hi"}):
                    yield event
            else:
                for event in _make_text_events("Done"):
                    yield event

        client.create_response = MagicMock(side_effect=lambda *a, **kw: fake_stream())

        async def mock_tool_executor(tc: ToolCall) -> str:
            return "hi"

        loop = AgentLoop(client=client, tool_executor=mock_tool_executor)
        result = await loop.run("run echo")
        assert result.output == "Done"
        assert call_count == 2

    async def test_max_iterations(self):
        client = MagicMock(spec=CodexClient)

        async def always_tool_call(*args, **kwargs):
            for event in _make_tool_call_events("bash", {"command": "loop"}):
                yield event

        client.create_response = MagicMock(side_effect=lambda *a, **kw: always_tool_call())

        async def mock_executor(tc: ToolCall) -> str:
            return "ok"

        loop = AgentLoop(client=client, tool_executor=mock_executor, max_iterations=3)
        result = await loop.run("loop forever")
        assert result.iterations == 3
```

**Implementation** (`packages/core/src/autogenesis_core/loop.py`):

```python
"""Agent loop — core execution engine.

Iterates: send messages to CodexClient → parse response → execute tool calls → repeat.
Streams text deltas to an optional display callback.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from pydantic import BaseModel, Field

from autogenesis_core.client import CodexClient
from autogenesis_core.events import Event, EventType, get_event_bus
from autogenesis_core.models import Message, ToolCall, ToolDefinition, TokenUsage
from autogenesis_core.responses import ResponseEventType

logger = structlog.get_logger()


class AgentLoopResult(BaseModel):
    """Result from a complete agent loop run."""

    output: str = ""
    usage: TokenUsage = Field(default_factory=TokenUsage)
    iterations: int = 0
    tool_calls_made: int = 0


class AgentLoop:
    """Async agent loop that drives the CodexClient."""

    def __init__(
        self,
        client: CodexClient,
        tool_executor: Callable[[ToolCall], Awaitable[str]] | None = None,
        tool_definitions: list[ToolDefinition] | None = None,
        instructions: str = "",
        max_iterations: int = 50,
        on_text_delta: Callable[[str], None] | None = None,
    ) -> None:
        self._client = client
        self._tool_executor = tool_executor
        self._tool_definitions = tool_definitions or []
        self._instructions = instructions
        self._max_iterations = max_iterations
        self._on_text_delta = on_text_delta

    async def run(self, prompt: str) -> AgentLoopResult:
        """Execute the agent loop for a given prompt."""
        bus = get_event_bus()
        messages: list[Message] = [Message(role="user", content=prompt)]
        total_usage = TokenUsage()
        total_tool_calls = 0

        bus.emit(Event(type=EventType.LOOP_EXECUTION_START, data={"prompt": prompt}))

        for iteration in range(1, self._max_iterations + 1):
            text_parts: list[str] = []
            tool_calls: list[ToolCall] = []

            bus.emit(Event(type=EventType.MODEL_CALL_START, data={"iteration": iteration}))

            async for event in self._client.create_response(
                messages=messages,
                instructions=self._instructions,
                tools=self._tool_definitions if self._tool_definitions else None,
            ):
                if event.event_type == ResponseEventType.OUTPUT_TEXT_DELTA:
                    delta = event.data.get("delta", "")
                    text_parts.append(delta)
                    if self._on_text_delta:
                        self._on_text_delta(delta)

                elif event.event_type == ResponseEventType.FUNCTION_CALL_ARGS_DONE:
                    call_id = event.data.get("call_id", "")
                    name = event.data.get("name", "")
                    args_str = event.data.get("arguments", "{}")
                    try:
                        args = json.loads(args_str)
                    except json.JSONDecodeError:
                        args = {"raw": args_str}
                    tool_calls.append(ToolCall(id=call_id, name=name, arguments=args))

                elif event.event_type == ResponseEventType.COMPLETED:
                    response = event.data.get("response", {})
                    usage = response.get("usage", {})
                    total_usage = total_usage + TokenUsage(
                        input_tokens=usage.get("input_tokens", 0),
                        output_tokens=usage.get("output_tokens", 0),
                        total_tokens=usage.get("total_tokens", 0),
                    )

            bus.emit(Event(type=EventType.MODEL_CALL_END, data={"iteration": iteration}))

            # If model produced text only (no tool calls), we're done
            if not tool_calls:
                output = "".join(text_parts)
                bus.emit(Event(type=EventType.LOOP_EXECUTION_END, data={"output": output[:200]}))
                return AgentLoopResult(
                    output=output,
                    usage=total_usage,
                    iterations=iteration,
                    tool_calls_made=total_tool_calls,
                )

            # Execute tool calls and add results to conversation
            if text_parts:
                messages.append(Message(role="assistant", content="".join(text_parts), tool_calls=tool_calls))
            else:
                messages.append(Message(role="assistant", content="", tool_calls=tool_calls))

            for tc in tool_calls:
                total_tool_calls += 1
                bus.emit(Event(type=EventType.TOOL_CALL_START, data={"tool": tc.name}))

                if self._tool_executor:
                    try:
                        result = await self._tool_executor(tc)
                    except Exception as exc:
                        result = f"Error: {exc}"
                else:
                    result = f"Error: No tool executor configured for {tc.name}"

                messages.append(Message(role="tool", content=result, tool_call_id=tc.id))
                bus.emit(Event(type=EventType.TOOL_CALL_END, data={"tool": tc.name}))

        # Max iterations reached
        bus.emit(Event(type=EventType.LOOP_EXECUTION_END, data={"reason": "max_iterations"}))
        return AgentLoopResult(
            output="Max iterations reached",
            usage=total_usage,
            iterations=self._max_iterations,
            tool_calls_made=total_tool_calls,
        )
```

### A4: Task 12 Step 4 — Full Chat Command Implementation (Important Fix)

```python
"""Chat command — interactive REPL with session persistence."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console

from autogenesis_cli.display import ApprovalManager, print_error, print_text_delta, print_text_done

console = Console()
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def chat_command(
    full_auto: bool = typer.Option(False, "--full-auto", help="Bypass all approval prompts"),
    model: str = typer.Option("gpt-5.3-codex", "--model", help="Model to use"),
    resume: str = typer.Option("", "--resume", help="Resume a previous session by ID"),
) -> None:
    """Interactive chat session with the agent."""
    asyncio.run(_chat_async(full_auto, model, resume))


async def _chat_async(full_auto: bool, model: str, resume: str) -> None:
    from autogenesis_core.client import CodexClient, CodexClientConfig
    from autogenesis_core.config import load_config
    from autogenesis_core.credentials import EnvCredentialProvider
    from autogenesis_core.loop import AgentLoop
    from autogenesis_core.models import Message
    from autogenesis_core.state import StatePersistence
    from autogenesis_tools.registry import ToolRegistry

    from autogenesis_tools.bash import BashTool
    from autogenesis_tools.filesystem import (
        FileEditTool, FileReadTool, FileWriteTool,
        GlobTool, GrepTool, ListDirTool,
    )
    from autogenesis_tools.think import ThinkTool

    config = load_config()
    provider = EnvCredentialProvider()
    client_config = CodexClientConfig(model=model)
    client = CodexClient(credential_provider=provider, config=client_config)

    registry = ToolRegistry()
    for tool_cls in [BashTool, FileReadTool, FileWriteTool, FileEditTool,
                     GlobTool, GrepTool, ListDirTool, ThinkTool]:
        registry.register(tool_cls())

    instructions = (_PROMPTS_DIR / "default.txt").read_text()
    approval = ApprovalManager(full_auto=full_auto)
    persistence = StatePersistence()
    messages: list[Message] = []

    if resume:
        state = persistence.load(resume)
        if state:
            messages = state.messages
            console.print(f"[blue]Resumed session {resume} ({len(messages)} messages)[/blue]")
        else:
            console.print(f"[yellow]Session {resume} not found, starting fresh.[/yellow]")

    console.print("[blue]AutoGenesis Chat[/blue] (type 'exit' or Ctrl+C to quit)\n")

    try:
        while True:
            try:
                user_input = console.input("[green]You>[/green] ").strip()
            except EOFError:
                break

            if not user_input or user_input.lower() in ("exit", "quit"):
                break

            messages.append(Message(role="user", content=user_input))

            tool_defs = registry.get_definitions_for_context()

            async def tool_executor(tc):
                tool = registry.get(tc.name)
                if not tool:
                    return f"Unknown tool: {tc.name}"
                if approval.should_prompt(tc.name):
                    if not approval.prompt_user(tc.name, tc.arguments):
                        return "Tool execution denied by user"
                return await tool(tc.arguments)

            loop = AgentLoop(
                client=client,
                tool_executor=tool_executor,
                tool_definitions=tool_defs,
                instructions=instructions,
                on_text_delta=print_text_delta,
            )

            result = await loop.run(user_input)
            print_text_done()

            messages.append(Message(role="assistant", content=result.output))
            console.print(f"[dim]({result.usage.total_tokens} tokens)[/dim]\n")

    except KeyboardInterrupt:
        console.print("\n[yellow]Session ended.[/yellow]")
    finally:
        await client.close()
```

### A5: Proactive Token Refresh (Important Fix — add to auth.py)

Add this function to `packages/core/src/autogenesis_core/auth.py`:

```python
def is_token_expiring(creds: OAuthCredentials, buffer_seconds: int = 300) -> bool:
    """Check if the access token expires within buffer_seconds (default 5 min)."""
    try:
        claims = _extract_claims(creds.access_token)
        exp = claims.get("exp")
        if exp is None:
            return False
        expiry = datetime.fromtimestamp(exp, tz=timezone.utc)
        return datetime.now(timezone.utc) >= expiry - timedelta(seconds=buffer_seconds)
    except Exception:
        return False
```

Add `from datetime import timedelta` to imports.

### A6: Logout Uses Public Function (Important Fix)

In `auth.py`, rename `_default_auth_path` → `get_credentials_path`:

```python
def get_credentials_path() -> Path:
    """Get the path where OAuth credentials are stored."""
    xdg = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(xdg) / "autogenesis" / "auth.json"
```

Update `logout.py` to import `get_credentials_path` instead of `_default_auth_path`.

### A7: Delete init.py CLI Command (Important Fix — add to Task 12)

Add to Task 12 Step 6 deletions:
```bash
rm packages/cli/src/autogenesis_cli/commands/init.py
```

### A8: SSE Stream Integration Test for CodexClient (Important Fix — add to test_client.py)

```python
class TestCodexClientStreaming:
    async def test_create_response_sync_collects_text(self):
        """Mock SSE stream and verify text collection."""
        provider = MockCredentialProvider()
        client = CodexClient(credential_provider=provider)

        events = [
            ("response.output_text.delta", json.dumps({"delta": "Hello "})),
            ("response.output_text.delta", json.dumps({"delta": "world"})),
            ("response.completed", json.dumps({"response": {"id": "r1", "usage": {"input_tokens": 5, "output_tokens": 2, "total_tokens": 7}}})),
        ]

        # Mock the aconnect_sse context to yield these events
        # Implementation detail: patch httpx_sse.aconnect_sse
        # The implementer should use unittest.mock.patch to mock the SSE connection
        # and yield ServerSentEvent-like objects with .event and .data attributes
        pass  # Implementer fills in mock details based on httpx-sse internals
```

### A9: Async Test Infrastructure (Important Fix — already configured)

The root `pyproject.toml` already has `asyncio_mode = "auto"` and `pytest-asyncio` in dev dependencies (line 13-14, 81). All `async def test_*` methods will run correctly without additional markers. No changes needed.

### A10: Breaking Model Changes Audit (Important Fix — apply during Task 2)

When rewriting `models.py`, audit these known consumers:

| Old field | Used in | Action |
|---|---|---|
| `Message.content: str \| list[ContentBlock]` | Always used as `str` in practice | Safe to change to `str` |
| `ToolResult.error: str \| None` | `loop.py` (line 162) | Change to `is_error: bool`, update loop |
| `AgentState.active_tools` | Not referenced outside models | Safe to remove |
| `AgentState.token_usage` | `loop.py` (line 202) | Remove, track in `AgentLoopResult` instead |
| `AgentState.model_config_name` | Not referenced outside models | Safe to remove |
| `ToolDefinition.tier_requirement` | `base.py` `to_definition()` | Update `to_definition()` to omit it |

### A11: Spec Deviations (Informational)

- SSE event type `OUTPUT_TEXT_DELTA` (`response.output_text.delta`) replaces spec's `CONTENT_PART_DELTA`. The plan uses the correct, more specific event type from the actual Responses API. Spec should be updated post-implementation.
- Device Code Flow is explicitly deferred (stretch goal per spec).
- `--json` and `--instructions` global flags are deferred to post-MVP. Not blocking.
