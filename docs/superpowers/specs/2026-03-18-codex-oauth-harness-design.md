# AutoGenesis Phase 2: Codex OAuth Agent Harness

## Overview

Reposition AutoGenesis as a fully-fledged autonomous agent harness powered by OpenAI Codex, authenticated via OAuth through a ChatGPT Plus subscription. No API-billed token usage — all requests route through the existing subscription.

## Execution Environment

AutoGenesis runs inside an isolated VM with full root access. The host machine is separate and inaccessible to the orchestrator.

- **Headless MVP**: CLI-only, no GUI. All interaction via terminal/SSH.
- **Future GUI mode**: Full desktop environment (Windows/macOS/Linux) where the orchestrator controls mouse, keyboard, and screen.
- **Secret management**: API keys, tokens, and passwords are stored on the host machine only. A custom gateway injects secrets into the VM opaquely — the orchestrator LLM never sees plaintext secrets.
- **Blast radius**: The VM is the sandbox. Tool execution is unrestricted within the VM. Security concerns focus on prompt injection and data exfiltration, not machine protection.

## Authentication

### Host-Side OAuth (PKCE Flow)

OAuth login happens on the host machine, not inside the VM.

1. User runs `autogenesis login` on host.
2. Local HTTP server starts on `localhost:1455`.
3. PKCE S256 codes generated (64 random bytes → base64url verifier → SHA256 → base64url challenge).
4. Browser opens to `https://auth.openai.com/authorize` with:
   - Client ID: `app_EMoamEEZ73f0CkXaXp7hrann`
   - Scopes: `openid profile email offline_access`
   - PKCE challenge, state, redirect URI
5. User authenticates → callback hits `/auth/callback` with authorization code.
6. Token exchange: POST `https://auth.openai.com/oauth/token` with authorization code + PKCE verifier.
7. JWT `id_token` parsed for `chatgpt_account_id` and `chatgpt_plan_type` from `https://api.openai.com/auth` claims.
8. Credentials stored at `$XDG_DATA_HOME/autogenesis/auth.json` with `0600` permissions.

### Device Code Flow (Headless Host)

For hosts without a browser. **Stretch goal** — these endpoints are derived from Codex CLI source code and may not be publicly documented. Verify availability before implementing; if unavailable, defer.

1. POST `https://auth.openai.com/deviceauth/usercode` with client ID.
2. Display user code + verification URL.
3. Poll `https://auth.openai.com/deviceauth/token` until authorized (15-minute timeout).
4. Same token exchange and storage as browser flow.

### Token Refresh

Two refresh triggers:

1. **Access token expiry** — Check the `exp` claim in the access token JWT. Proactively refresh when within 5 minutes of expiry. Also triggered reactively on 401 from the API.
2. **Refresh token rotation** — Every 8 days (matching Codex CLI's cadence), rotate the refresh token via POST to `https://auth.openai.com/oauth/token` with `grant_type=refresh_token`.

- On permanent failure (expired, revoked, invalidated): prompt re-login.
- On transient failure (network): retry with backoff.
- Refresh happens host-side; gateway pushes updated tokens to VM.

### Data Models

```python
class OAuthCredentials(BaseModel):
    access_token: str
    refresh_token: str
    id_token: str
    account_id: str
    plan_type: str
    last_refresh: datetime

class AuthConfig(BaseModel):
    client_id: str = "app_EMoamEEZ73f0CkXaXp7hrann"
    auth_base_url: str = "https://auth.openai.com"
    storage_path: Path  # $XDG_DATA_HOME/autogenesis/auth.json
```

## VM-Side Credential Provider

AutoGenesis inside the VM does not perform OAuth. It consumes credentials from the gateway via an abstraction:

```python
class CredentialProvider(ABC):
    async def get_access_token(self) -> str: ...
    async def get_account_id(self) -> str: ...
```

Three implementations:
- **`GatewayCredentialProvider`** (MVP): Reads from a mounted file at a well-known path (`/run/autogenesis/credentials.json`), refreshed by the host-side gateway. The file contains `{"access_token": "...", "account_id": "..."}` and is overwritten atomically by the host when tokens are refreshed. The provider reads fresh on each call.
- **`FileCredentialProvider`**: Reads `auth.json` directly (for local dev / host-side usage without VM).
- **`EnvCredentialProvider`**: Reads `AUTOGENESIS_ACCESS_TOKEN` + `AUTOGENESIS_ACCOUNT_ID` env vars (simplest integration, static credentials).

The provider is stateless — reads fresh on each call. If the gateway refreshes tokens, AutoGenesis picks them up automatically. No token persistence inside the VM.

## API Client (Responses API)

New `CodexClient` class replaces the existing `ModelRouter` + LiteLLM.

- Calls `POST https://api.openai.com/v1/responses` with SSE streaming.
- Headers: `Authorization: Bearer {access_token}`, `ChatGPT-Account-ID: {account_id}`.
- Tools sent in Responses API format: `{"type": "function", "name": "...", "description": "...", "parameters": {...}}`. Strict mode deferred — existing tool schemas need `additionalProperties: false` and all properties in `required` to comply. For MVP, omit `strict` flag.
- Parses SSE events, yields `ResponseEvent` objects. See SSE Event Model below.
- Single model, configurable (default `gpt-5.3-codex`). No tier routing.
- Retry on 429/5xx with exponential backoff (1s/2s/4s). Consumes `retry-after` and `x-ratelimit-*` headers when present.
- On 401: signal credential provider to refresh (proactive refresh when access token `exp` claim is within 5 minutes of expiry).

### SSE Event Model

The Responses API uses server-sent events with a different taxonomy than Chat Completions. Events to handle:

```python
class ResponseEventType(StrEnum):
    RESPONSE_CREATED = "response.created"
    OUTPUT_ITEM_ADDED = "response.output_item.added"
    CONTENT_PART_ADDED = "response.content_part.added"
    CONTENT_PART_DELTA = "response.content_part.delta"        # text deltas
    CONTENT_PART_DONE = "response.content_part.done"
    FUNCTION_CALL_ARGS_DELTA = "response.function_call_arguments.delta"  # tool call args streaming
    FUNCTION_CALL_ARGS_DONE = "response.function_call_arguments.done"    # tool call complete
    OUTPUT_ITEM_DONE = "response.output_item.done"
    COMPLETED = "response.completed"
    FAILED = "response.failed"
    RATE_LIMITED = "response.rate_limited"

class ResponseEvent(BaseModel):
    event_type: ResponseEventType
    data: dict[str, Any]
```

### Conversation Format

The Responses API uses a different conversation format than Chat Completions. Instead of `role: "user"/"assistant"/"tool"` messages, it uses typed items:

- `{"type": "message", "role": "user", "content": [...]}` — user messages
- `{"type": "function_call", "name": "...", "arguments": "...", "call_id": "..."}` — tool calls from model
- `{"type": "function_call_output", "call_id": "...", "output": "..."}` — tool results

The `CodexClient` translates between AutoGenesis's internal `Message` model and the Responses API item format. The `Message` model remains Chat Completions-shaped internally for simplicity; translation happens at the API boundary.

### Error Handling

API errors are parsed from the SSE stream or HTTP response body:

```python
class APIError(BaseModel):
    status_code: int
    error_type: str   # "rate_limit_error", "authentication_error", "server_error", etc.
    message: str
    retry_after: float | None = None  # from header or response body
```

Errors propagate to the agent loop as exceptions: `AuthenticationError` (401), `RateLimitError` (429), `ServerError` (5xx). The loop handles each: re-auth on 401, backoff on 429, retry on 5xx.

### Key Differences from Current Router

| Current (`ModelRouter` + LiteLLM) | New (`CodexClient`) |
|---|---|
| Multi-provider abstraction | Single provider (OpenAI Codex) |
| 3-tier routing with fallback chains | Single model, configurable |
| Chat Completions API | Responses API |
| LiteLLM dependency | Direct httpx + SSE |
| API key auth | OAuth access token + account ID |

## Agent Loop

The existing `AgentLoop` is retained with modifications:

- Constructor takes `CodexClient` instead of `ModelRouter`.
- Calls `client.create_response()` instead of `router.complete()`.
- Passes tool definitions from `registry.get_definitions_for_context()` to each `create_response()` call.
- Parses Responses API tool call format (function_call items, not Chat Completions tool_calls).
- Streams text deltas to display layer.
- Keeps: event emission, state persistence, context management, max iterations, cancellation.
- Budget enforcement: with subscription billing there is no per-token cost. Budget tracking switches to **token count only** (no USD cost). Session/daily limits expressed in tokens, not dollars.

## Sub-Agent Support

New `SubAgentManager` class for supervised Codex CLI subprocess orchestration.

- Spawns `codex` CLI as async subprocess: `codex --quiet --full-auto "task"`.
- Supervised: tracks each subprocess, can cancel via `proc.terminate()`.
- Collects structured output (stdout/stderr + exit code).
- Concurrency limit: default 3 parallel sub-agents.
- Depth limit: max 2 levels. Enforced via `AUTOGENESIS_AGENT_DEPTH` environment variable, incremented on each spawn. Sub-agents spawned as Codex CLI processes do not have access to the `sub_agent` tool (they run vanilla Codex), so depth enforcement is inherent — Codex sub-agents cannot spawn AutoGenesis sub-sub-agents.
- Working directory isolation: each sub-agent gets its own cwd.

The existing `sub_agent` tool stub is wired to `SubAgentManager`:

```
Tool call: sub_agent(task="fix the failing tests", cwd="/project/tests")
→ Spawns: codex --quiet --full-auto "fix the failing tests"
→ Monitors: stream output, track progress
→ Returns: structured result (output, files changed, exit code)
```

## Tools (MVP)

### Keep (9 tools)

| Tool | Purpose |
|---|---|
| `bash` | Shell execution (unrestricted in VM) |
| `file_read` | Read files with optional line range |
| `file_write` | Write files, create directories |
| `file_edit` | Replace exact string matches |
| `glob` | Find files by pattern |
| `grep` | Search file contents with regex |
| `list_dir` | Directory listing |
| `think` | Reasoning scratchpad |
| `sub_agent` | Delegate tasks to Codex CLI subprocess |

### Remove from MVP

| Tool | Reason |
|---|---|
| `ask_user` | Blocking `input()` incompatible with headless. Reimplement later with async message queue. |
| `web_fetch` | Stub returning "disabled". Remove until properly implemented. |
| `mcp_call` | MCP package deferred. |

### Tool Interface Changes

- Add `to_responses_api_format()` method to `Tool` ABC.
- Remove `tier_requirement` property (no tiers).
- Keep `hidden` and `token_cost_estimate` for progressive disclosure.
- Registry: remove tier-based filtering, keep budget + frequency-based progressive disclosure.

## CLI (MVP)

### Commands

| Command | Description |
|---|---|
| `autogenesis login` | Host-side OAuth PKCE flow. `--device-code` for headless. |
| `autogenesis logout` | Wipe stored credentials. |
| `autogenesis run "task"` | Single-shot execution. Streams output. `--full-auto` bypasses approval. Reads stdin if no argument. |
| `autogenesis chat` | Interactive REPL. Session state saved. `--resume <id>` to continue. |
| `autogenesis config show/get/set` | Configuration management. |

### Removed from MVP

`optimize`, `scan`, `audit`, `tokens`, `plugins`, `mcp`, `init` — all stubs or unnecessary for MVP.

### Global Flags

| Flag | Effect |
|---|---|
| `--full-auto` | Bypass all tool approval prompts |
| `--model <id>` | Override model (default `gpt-5.3-codex`) |
| `--quiet` | Minimal output, pipe-friendly |
| `--json` | Structured JSON output |

### Display Layer

Rich-based streaming output:
- Text deltas rendered as they arrive.
- Tool calls: show tool name + arguments, then result.
- Approval prompts: `[Allow] bash: rm -rf /tmp/build? [y/n/always]` — "always" auto-approves that tool for session.
- Headless-compatible: works in plain terminal, no TUI framework.

## Package Changes

### Modify for MVP

| Package | Changes |
|---|---|
| `core` | Replace `router.py` with `client.py` (CodexClient). Add `auth.py` (host-side OAuth), `credentials.py` (CredentialProvider ABC). Simplify `models.py` (remove ModelTier, ContentBlock, PromptVersion). Keep loop, events, state, context. |
| `tools` | Keep registry + 9 tools. Add `to_responses_api_format()`. Remove ask_user, web_fetch, mcp_call. Wire sub_agent to SubAgentManager. Move think to own module. |
| `cli` | Rewrite commands (login, logout, run, chat, config). New display layer. Remove stub commands. |

### Defer (No Changes for MVP)

| Package | Status |
|---|---|
| `tokens` | Budget/cache/compression work as-is. Counter needs tiktoken rewrite but not urgent with subscription billing. |
| `security` | Guardrails/audit valuable post-MVP. VM is the sandbox for now. |
| `plugins` | Clean interface, works as-is. Re-integrate for extensibility. |
| `mcp` | Client mode useful later. Server mode likely removed. |

### Remove

| Package | Reason |
|---|---|
| `optimizer` | Text-matching evaluation is fundamentally broken. Needs full rewrite with LLM-based evaluation. Not MVP scope. |

## Dependency Changes

| Remove | Add | Keep |
|---|---|---|
| `litellm` | `httpx` (async HTTP), `httpx-sse` (SSE parsing) | `pydantic` |
| | | `typer` |
| | | `rich` |
| | | `structlog` |
| | | `pyyaml` |

## System Prompt

The `AgentLoop` takes an `instructions` parameter (Responses API terminology, replaces `system_prompt`). For MVP, this is a hardcoded default in the CLI that describes AutoGenesis's capabilities and tool usage patterns. Stored at `packages/cli/src/autogenesis_cli/prompts/default.txt`. Overridable via `--instructions <file>` flag or config.

## Migration Notes

- Existing persisted session state files (from v0.1.0) are incompatible with the new models. Old state files are abandoned — no migration path. The `StatePersistence` module will simply fail to load old format and start fresh.
- The `think` tool currently lives in `web.py` alongside `WebFetchTool`. Since `web_fetch` is removed, `think` moves to its own `think.py` module.

## Design Constraints

- All interfaces must be display-agnostic (no terminal-only assumptions) to support future GUI mode.
- No secrets stored or logged inside the VM.
- Progressive tool disclosure (budget + frequency) is retained as a differentiator.
- Event bus architecture retained for observability and extensibility.
- Pydantic V2 for all data models.
- XDG Base Directory compliance for all paths.
