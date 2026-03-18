# AutoGenesis v0.1.0 Design Specification

**Date:** 2026-03-17
**Status:** Approved
**Target:** v0.1.0 release

## Overview

AutoGenesis is a CLI-first, token-efficient, self-improving agentic workflow framework. It is a Python CLI tool that orchestrates LLM-powered agent workflows with five core pillars:

1. **Iterative Self-Improving System Prompts** — the agent refines its own prompts over time
2. **Token Efficiency Optimization** — every operation minimizes token consumption
3. **Hardware Efficiency Optimization** — resource-aware scheduling and monitoring
4. **Proactive Security & Self-Pentesting** — autonomous vulnerability scanning
5. **CLI-First Architecture** — command-line tool orchestrating all capabilities

**Tagline:** "The token-efficient agent framework. CLI-first. Self-improving. Every token counts."

## Architectural Constraints

- Core runtime < 2,000 lines of code
- Single-threaded master loop (while-loop continues while model response includes tool calls; terminates on plain text)
- 12 built-in atomic tools (max 20 built-in); MCP and plugin tools are additive but governed by progressive disclosure token budget, not this count
- Python 3.11+ with Typer + Rich for CLI, Pydantic V2 for all data models
- LiteLLM for model-agnostic provider access
- MCP client + MCP server from day one (via FastMCP + official mcp SDK)
- MIT License
- XDG Base Directory compliant: all paths respect `XDG_CONFIG_HOME` (config), `XDG_DATA_HOME` (plugins), `XDG_STATE_HOME` (sessions, budgets, audit logs), `XDG_CACHE_HOME` (cache DB), falling back to their standard defaults
- Every abstraction is opt-in; debuggability over convenience

## Package Architecture

8-package uv workspace monorepo:

```
autogenesis/
├── packages/
│   ├── core/          # Agent runtime, master loop, state, models, config, events
│   ├── tools/         # Built-in tool definitions, registry, progressive disclosure
│   ├── tokens/        # Token counting, budgeting, caching, compression, reporting
│   ├── optimizer/     # Self-improving prompt engine, versioning, evaluation
│   ├── security/      # Guardrails, sandboxing, audit logging, scanning
│   ├── mcp/           # MCP client + server implementations
│   ├── plugins/       # Plugin interface, loader, built-in plugins
│   └── cli/           # Typer CLI application, all commands
├── prompts/           # Version-controlled prompt templates
├── examples/          # Self-contained example scripts
├── docs/              # MkDocs Material documentation
├── tests/             # Integration + E2E tests
├── scripts/           # Dev setup, benchmarks
└── .github/           # CI/CD workflows, templates
```

### Dependency Graph

```
cli → [core, tools, tokens, optimizer, security, mcp, plugins]
core → (nothing internal — owns SandboxProvider ABC)
tools → core, mcp
tokens → core
optimizer → core, tokens
security → core (provides concrete sandbox implementations)
mcp → core
plugins → core, tools
```

**Design decision:** All MCP logic lives in `packages/mcp/`. The `mcp_call` built-in tool lives in `packages/tools/` but delegates to `packages/mcp/`, making tools depend on mcp. This eliminates the duplication of having `mcp_client.py` in both packages.

**Design decision (sandbox injection):** The `SandboxProvider` ABC and its interface live in `packages/core/` (as `core/sandbox.py`), not in `packages/security/`. This breaks the circular dependency: `tools` imports the sandbox interface from `core`, and `security` provides concrete sandbox implementations that are injected at startup. The `security` package depends on `core` (for the ABC) and `tools` depends on `core` (for the ABC) — no cycle.

## Core Runtime (packages/core/)

### Data Models (models.py)

All data flows through Pydantic V2 models with strict validation:

- **Message** — role (system/user/assistant/tool), content (str or ContentBlock list), optional tool_calls, token_count, timestamp
- **ContentBlock** — type (text/image/tool_use/tool_result) with associated fields
- **ToolCall** — id (auto-generated), name, arguments dict
- **ToolResult** — tool_call_id, output string, optional error, token_count, execution_time_ms
- **AgentState** — complete serializable agent state: session_id, messages, active_tools, token_usage, model config, metadata, timestamps
- **TokenUsage** — input/output/cache_read/cache_write tokens, total_cost_usd, api_calls, computed total_tokens property
- **ModelTier** — enum: FAST, STANDARD, PREMIUM
- **ToolDefinition** — name, description, JSON Schema parameters, tier_requirement, token_cost_estimate (the number of tokens the tool's JSON definition consumes when included in the model context — computed at registration time by counting the serialized definition)
- **PromptVersion** — semver version, content, SHA-256 checksum, parent_version, metrics, is_active, is_constitutional flag

### Configuration (config.py)

XDG-compliant configuration with 6-layer cascade (later overrides earlier):

1. Built-in defaults (hardcoded)
2. System config: `/etc/autogenesis/config.yaml`
3. User config: `~/.config/autogenesis/config.yaml` (XDG_CONFIG_HOME)
4. Project config: `.autogenesis/config.yaml` (cwd, walk up to git root)
5. Environment variables: `AUTOGENESIS_*` (nested via `__` separator)
6. CLI flags (`--model`, `--max-tokens`, etc.)

Uses `pydantic-settings` for env var parsing. Config file format: YAML via PyYAML.

Top-level config sections: `models`, `tokens`, `security`, `telemetry`, `mcp`.

### Model Router (router.py)

Wraps LiteLLM to provide 3-tier model routing:

- **FAST:** gpt-4o-mini, claude-haiku, gemini-flash (< $0.50/M tokens)
- **STANDARD:** claude-sonnet, gpt-4o, gemini-pro ($1-5/M tokens)
- **PREMIUM:** claude-opus, o3, gemini-ultra ($5+/M tokens)

Features:
- Configurable primary + fallback models per tier
- Routing strategies: tier-based, cost-optimized, latency-optimized
- Auto-upgrade/downgrade based on task complexity
- Every call returns `CompletionResult` with full token usage, latency, cache hit info
- Budget enforcement: raises `TokenBudgetExceeded` before making call if estimated cost exceeds budget
- Prompt caching hints for Anthropic models
- All LiteLLM types converted to AutoGenesis Pydantic models at the boundary
- **Retry strategy:** 3 retries with exponential backoff (1s, 2s, 4s) for transient errors (rate limits, network timeouts, 5xx). No retry on 4xx (auth, validation). Fallback to next model in tier's fallback list after all retries exhausted. If all models in tier unavailable, raise `AllModelsUnavailable` with list of attempted models and errors.

### Master Agent Loop (loop.py)

Single-threaded master loop following the Claude Code pattern. The loop is `async def` running on a single asyncio event loop (all I/O uses `await`), but tool execution within each iteration is sequential (`for tool_call in tool_calls: await execute(tool_call)`). The CLI entry point uses `asyncio.run()` to drive the loop.

```python
async def run(self, user_message: str, ...) -> AgentLoopResult:
    # append user message to state
    while True:
        response = await self.router.complete(...)  # async I/O
        if not response.message.tool_calls:
            break  # plain text → done
        for tool_call in response.message.tool_calls:
            result = await self._execute_tool(tool_call)  # sequential
            # append result to state
        # check termination conditions
    return AgentLoopResult(...)
```

Termination conditions:
- Model returns text without tool_calls
- max_iterations reached (default 50)
- Token budget exhausted
- User cancels (Ctrl+C)

Every iteration: updates AgentState.token_usage, auto-saves state for crash recovery, emits events.

### State Persistence (state.py)

Session state is persisted as JSON files:
- **Location:** `$XDG_STATE_HOME/autogenesis/sessions/{session_id}.json` (default `~/.local/state/autogenesis/sessions/`)
- **Format:** JSON serialization of `AgentState` via Pydantic's `.model_dump_json()`
- **Auto-save:** After each loop iteration, state is written atomically (write to temp file, then rename) for crash recovery
- **Recovery:** On `autogenesis chat --resume <session_id>`, load the JSON file and reconstruct `AgentState`. If the session file exists but the last iteration didn't complete, the state reflects the last successful iteration.
- **Cleanup:** Sessions older than 30 days are pruned on startup (configurable via `core.session_retention_days`). `autogenesis config set core.session_retention_days 7` to change.
- **Listing:** `autogenesis chat --list-sessions` shows available sessions with timestamps and message counts.

### Context Manager (context.py)

Sliding window strategy:
1. Always include: system prompt + tool definitions (top of context)
2. Always include: last 10 turns verbatim
3. If over budget: **drop oldest turns** (not summarize — no LLM calls in core loop)
4. Never drop system prompt or tool definitions

**Design decision:** Summarization of old turns requires LLM calls, adding cost and latency. For v0.1.0, context management uses pure truncation. A summarization hook is available for future integration via the compression module.

### Event System (events.py)

Synchronous pub/sub with 12 event types (consistent `domain.subject.action` naming):
- loop.execution.start, loop.execution.iteration, loop.execution.end
- tool.call.start, tool.call.end
- model.call.start, model.call.end
- token.budget.warning, token.budget.exceeded
- prompt.version.change
- security.guardrail.alert
- context.window.truncation

Exception-safe handlers (log and continue on handler errors). Global singleton via `get_event_bus()`. All events are Pydantic models.

## Tools & MCP (packages/tools/, packages/mcp/)

### Built-in Tools (12 total)

1. **bash** — shell execution with timeout (30s default), ANSI stripping, output truncation
2. **file_read** — read with line ranges, truncation, metadata
3. **file_write** — create/write with auto-mkdir, diff output
4. **file_edit** — str_replace pattern editing
5. **glob** — pattern matching respecting .gitignore
6. **grep** — regex search with context lines, respecting .gitignore
7. **list_dir** — directory listing with depth limit
8. **web_fetch** — URL fetching with HTML→markdown conversion (disabled by default, requires explicit opt-in via `security.tools.web_fetch.enabled: true`)
9. **think** — no-op tool for structured reasoning; content appended to context but not displayed to user
10. **ask_user** — request human input (y/n, free text, selection)
11. **sub_agent** — stub for v0.1.0, raises `NotImplementedError("Sub-agent support coming in v0.3.0")`. **Hidden from model context:** the stub is registered in the registry but excluded from `get_definitions_for_context()` to avoid wasting tokens on a non-functional tool. It exists only so the registry is ready for v0.4.0 activation.
12. **mcp_call** — invoke MCP tool, delegates to mcp package

All tools: validate arguments against JSON schema, return strings only, track execution time, emit events, handle errors gracefully (return error string, never raise).

### Tool Registry (registry.py)

Progressive disclosure — the key token efficiency mechanism for tools:
- Tool definitions consume ~200-500 tokens each
- Loading all 12 = ~4000 tokens; loading only 4 most relevant = ~1500 tokens
- `get_definitions_for_context(token_budget, required, hints)` returns tool definitions that fit within budget
- Required tools always included, then prioritized by relevance score
- **Relevance scoring:** (1) tools listed in `required` get priority 0 (always included), (2) tools matching keywords in `hints` list (matched against tool name + description) get priority 1, (3) tools with highest usage frequency in current session get priority 2, (4) remaining tools alphabetically get priority 3. Load in priority order until token budget exhausted.
- Tools with `hidden=True` (e.g., `sub_agent` stub) are excluded from context entirely

### MCP Client (packages/mcp/client.py)

Connect to external MCP servers (stdio or SSE transport). Features:
- Lazy tool loading — don't fetch all definitions upfront
- Connect/disconnect/list_tools/call_tool/list_resources/read_resource
- Environment variable substitution in server configs

### MCP Server (packages/mcp/server.py)

Via FastMCP, exposes AutoGenesis capabilities as MCP tools:
- autogenesis_run, autogenesis_optimize, autogenesis_tokens_report, autogenesis_scan

### MCP Registry (packages/mcp/registry.py)

Allowlist enforcement (block unlisted servers by default), server health checking, connection pooling.

## Token Efficiency (packages/tokens/)

### Counter (counter.py)
Cross-provider token counting via LiteLLM's `token_counter()`. Cost estimation per model.

### Budget (budget.py)
Session/daily/monthly budgets. Alerts at 80%, hard stop at 100%. Per-agent budgets for sub-agents. Persistent tracking in `~/.local/state/autogenesis/budgets.json`.

### Cache (cache.py)
Exact-match cache (hash of messages → response). SQLite in `~/.cache/autogenesis/cache.db`. Configurable TTL (default 1 hour). Cache invalidation on prompt version change.

**Design decision:** No embedding-based semantic similarity cache in v0.1.0. Deterministic exact-match only.

### Compression (compression.py)
Interface for context compression. v0.1.0 implementation: truncate old tool outputs, observation masking (`[output truncated — N tokens]`). Pluggable summarization hook for future LLM-based summarization.

### Reporter (reporter.py)
Per-session summary, per-tool breakdown, historical trends. Export: JSON, CSV, Rich table.

## Self-Improving Prompts (packages/optimizer/)

### Versioning (versioning.py)
YAML-based prompt storage in `prompts/` directory. Semver versioning with SHA-256 checksums. Git-backed history. Multiple environments (dev/staging/prod). Rollback support.

**`prompts/manifest.yaml` schema:**
```yaml
prompts:
  core:                           # prompt name (matches filename in prompts/system/)
    active_version: "1.2.0"       # currently active semver
    active_environment: "prod"    # dev | staging | prod
    versions:
      "1.2.0":
        checksum: "sha256:abc..."
        created_at: "2026-03-17T00:00:00Z"
        metrics:
          task_completion: 4.2
          token_efficiency: 3.8
          safety_compliance: 5.0
          coherence: 4.5
      "1.1.0":
        checksum: "sha256:def..."
        created_at: "2026-03-15T00:00:00Z"
        metrics: { ... }
  constitution:
    active_version: "1.0.0"
    locked: true                  # constitutional prompts cannot be modified
    versions:
      "1.0.0":
        checksum: "sha256:ghi..."
        created_at: "2026-03-17T00:00:00Z"
```

### Constitution (constitution.py)
`prompts/system/constitution.yaml` contains immutable safety rules. Validated before AND after every prompt modification. Any violating prompt is automatically rejected. Rules cannot be modified by the optimizer.

**`prompts/system/constitution.yaml` schema:**
```yaml
version: "1.0.0"
rules:
  - id: "CONST-001"
    description: "Never execute commands that delete system files"
    pattern: "rm\\s+(-rf?\\s+)?/"    # regex to detect in generated commands
    type: "output_block"              # output_block | input_block | behavior
    severity: "critical"
  - id: "CONST-002"
    description: "Always confirm destructive operations with the user"
    type: "behavior"
    severity: "critical"
  - id: "CONST-003"
    description: "Never exfiltrate data to external URLs without explicit permission"
    pattern: "curl|wget|requests\\.post"
    type: "output_block"
    severity: "critical"
  - id: "CONST-004"
    description: "Always display token costs to the user"
    type: "behavior"
    severity: "high"
checksum: "sha256:..."              # self-integrity check
```

### Evaluator (evaluator.py)
LLM-as-judge scoring (1-5) on: task_completion, token_efficiency, safety_compliance, coherence. Golden test suite in `prompts/tests/`. Regression detection: new prompt must score >= previous.

### Engine (engine.py)
`critique_revise` strategy (default, no external deps):
1. Run current prompt against test suite → baseline
2. LLM critiques failures
3. Generate N candidate prompts
4. Evaluate each against test suite
5. Promote best if it beats baseline on all metrics
Budget: $5 per optimization run (tracked separately from runtime costs).

### Drift Detection (drift.py)
**Design decision:** v0.1.0 uses metric score comparison only (LLM-as-judge scores from evaluator). No embedding-based cosine similarity. If scores drop below threshold vs baseline, flag drift.

## Security (packages/security/)

### Guardrails (guardrails.py)
Pattern/regex-based, zero LLM cost:
- **Input:** prompt injection detection, PII detection (SSN, credit card, email), content length limits
- **Output:** dangerous command detection (rm -rf, DROP TABLE), URL exfiltration detection
- Composable with AND/OR logic. Returns `GuardrailResult(passed, reason, severity)`.

### Allowlist (allowlist.py)
Default: all built-in tools allowed, all MCP servers blocked. Per-project allowlist. Per-tool permission model. MCP server allowlist with hash pinning.

### Audit (audit.py)
JSON Lines in `~/.local/state/autogenesis/audit/`. SHA-256 hash chain (each entry includes hash of previous entry). Daily rotation, 30-day retention. Query via `autogenesis audit show`.

### Scanner (scanner.py)
Built-in adversarial test suite. Tests prompt injection, jailbreak, data exfiltration attempts. Reports pass/fail with security score. Optional Promptfoo/Garak integration.

### Sandbox Implementations (sandbox.py)
The `SandboxProvider` ABC lives in `packages/core/sandbox.py` (see dependency graph design decision). This package provides the concrete implementations:
- **SubprocessSandbox** (default): restricted PATH, timeout, no network for bash tool
- **DockerSandbox** (opt-in)
- **E2BSandbox** (opt-in, requires API key)

## Plugins (packages/plugins/)

### Interface (interface.py)
`PluginManifest` (Pydantic): name, version, description, permissions list, token_budget (max tokens for tool definitions). `Plugin` ABC: `get_tools()`, `on_load()`, `on_unload()`.

### Loader (loader.py)
Discovery order: Python entry points → PATH-based (`~/.local/share/autogenesis/plugins/`) → project-local (`.autogenesis/plugins/`). Validates manifests, checks permissions against allowlist, enforces token budgets, registers tools.

## CLI (packages/cli/)

Typer application with Rich output formatting.

### Commands
- `autogenesis chat` — interactive chat with token display, session resume, Ctrl+C handling
- `autogenesis run <task>` — single-shot execution, supports piping, returns exit codes
- `autogenesis init` — interactive project setup wizard
- `autogenesis config show|set` — configuration management
- `autogenesis optimize run|check|rollback|history` — prompt optimization
- `autogenesis scan` — security scanning
- `autogenesis tokens report|history|budget` — token usage reporting
- `autogenesis plugins list|install|remove` — plugin management
- `autogenesis mcp list|connect|disconnect|test` — MCP server management
- `autogenesis audit show [--since 1h] [--type tool.call]` — audit log query

All commands: `--json` flag for machine output, Rich formatting, graceful error handling, progress indicators.

### Display (display.py)
Markdown rendering, syntax-highlighted code, tool execution spinners, token usage bar (budget consumed/remaining). Compact mode (`--quiet`) for scripting.

## Execution Plan

**Approach A: Phase-Sequential, Subagent-Parallel**

6 phases executed sequentially. Subagents within each phase dispatched in parallel. Quality gates (all-or-nothing) block progression between phases. Max 3 iterations per gate (5 for final gate).

### Phase 1: Scaffolding & Infrastructure
- 1A: Monorepo skeleton (parallel)
- 1B: Community & governance files (parallel)
- 1C: CI/CD pipeline (parallel)
- 1D: Developer tooling (parallel)
- **Gate 1:** 10/10 checks

### Phase 2: Core Runtime & Data Models
- 2A: Pydantic models & config (parallel with 2B)
- 2B: LiteLLM router (parallel with 2A)
- 2C: Master agent loop (depends on 2A, 2B)
- 2D: Event system (depends on 2A)
- **Gate 2:** 12/12 checks

### Phase 3: Tools & MCP
- 3A: Tool registry & built-in tools (parallel with 3B)
- 3B: MCP client & server (parallel with 3A)
- 3C: CLI commands (depends on 3A, 3B)
- **Gate 3:** 12/12 checks

### Phase 4: Token Efficiency & Self-Improvement
- 4A: Token efficiency stack (parallel with 4B)
- 4B: Self-improving prompt engine (parallel with 4A)
- **Gate 4:** 10/10 checks

### Phase 5: Security & Plugins
- 5A: Security guardrails & audit (parallel with 5B)
- 5B: Plugin architecture (parallel with 5A)
- 5C: Remaining CLI commands (depends on 5A, 5B)
- **Gate 5:** 10/10 checks

### Phase 6: Integration, Polish & Release
- 6A: Integration & E2E tests (parallel)
- 6B: Documentation (parallel)
- 6C: Benchmarks & examples (parallel)
- **Gate 6 (Final):** 15/15 checks → tag v0.1.0

### Quality Gate Definitions

**Gate 1 (10 checks):** (1) `uv sync` exits 0, (2) `ruff check packages/` exits 0, (3) `mypy packages/` exits 0, (4) `pytest --collect-only` discovers test dirs in all 8 packages, (5) all packages import cleanly, (6) `dev-setup.sh` runs successfully, (7) all .md files render valid markdown, (8) `.github/workflows/*.yml` pass actionlint, (9) no circular imports, (10) LICENSE contains MIT text with correct year.

**Gate 2 (12 checks):** (1) `pytest packages/core/tests/` all pass, (2) AgentLoop completes mock conversation (3 turns, 2 tool calls), (3) TokenUsage accumulates correctly, (4) config loads from YAML + env vars with correct precedence, (5) ContextManager keeps context under budget with 50-message conversation, (6) ModelRouter falls back when primary raises, (7) AgentState round-trips through JSON, (8) EventBus delivers events to all subscribers, (9) `mypy packages/core/` strict passes, (10) `ruff check packages/core/` exits 0, (11) core test coverage >= 80%, (12) no function exceeds 50 lines.

**Gate 3 (12 checks):** (1) `autogenesis chat` completes 3-turn mock conversation, (2) `autogenesis run` uses bash tool correctly, (3) tool registry loads only tools within token budget, (4) MCP client connects to mock server, (5) token usage reporting is accurate, (6) all CLI commands have --help, (7) config cascade works end-to-end, (8) AgentState persists and resumes, (9) all tests pass, (10) coverage >= 80%, (11) mypy strict zero errors, (12) e2e echo test returns correct answer.

**Gate 4 (10 checks):** (1) budget enforcement stops agent at limit, (2) exact-match cache saves tokens, (3) compression reduces tokens >= 30%, (4) `autogenesis tokens report` shows accurate breakdown, (5) prompt optimization generates improved candidate, (6) constitutional rules cannot be bypassed, (7) prompt versioning creates correct chain, (8) drift detection fires on degraded prompt, (9) `autogenesis optimize run` completes within budget, (10) coverage >= 80% for tokens + optimizer.

**Gate 5 (10 checks):** (1) prompt injection detection catches >= 5 patterns, (2) dangerous command detection flags rm -rf / DROP TABLE, (3) MCP allowlist blocks unlisted servers, (4) audit log hash chain validates, (5) `autogenesis scan` produces report, (6) plugin loads via entry point, (7) plugin with excessive permissions rejected, (8) all CLI commands work, (9) coverage >= 80% for security + plugins, (10) full integration test passes.

**Gate 6 (15 checks):** (1) all tests pass, (2) coverage >= 80% all packages, (3) mypy strict zero errors, (4) ruff zero violations, (5) `uv build` succeeds all packages, (6) wheel installs in clean venv + `autogenesis --help` works, (7) mkdocs build no warnings, (8) all examples run, (9) benchmark suite produces results, (10) security scan >= 80% score, (11) audit hash chain validates after integration test, (12) README badges/links resolve, (13) CHANGELOG has v0.1.0 entry, (14) conventional commits throughout, (15) no TODO/FIXME/HACK in production code.

## Roadmap

v0.1.0 ships ALL 8 packages with the full feature set described in this spec. The roadmap below describes post-v0.1.0 enhancements:

- **v0.1.0:** All 8 packages: core runtime, CLI, tools, MCP, tokens, optimizer, security, plugins — the complete framework as specified in this document
- **v0.2.0:** Semantic similarity cache (embedding-based), LLMLingua-2 compression, LLM-based context summarization
- **v0.3.0:** Sub-agent parallelism (activate sub_agent tool — currently stubbed), multi-agent orchestration patterns
- **v0.4.0:** Efficiency dashboard TUI, edge deployment optimizations
- **v0.5.0:** Community plugin marketplace, advanced routing strategies
- **v1.0.0:** Production-ready, full external security audit, stable API guarantee

## Global Constraints

- Python 3.11+ modern syntax (match/case, X | Y unions)
- Type hints everywhere, mypy strict
- Pydantic V2 for all data models
- Async-first I/O: core loop and all I/O operations are `async def` running on a single asyncio event loop. CLI entry points use `asyncio.run()` at the top level. Tool execution within each loop iteration is sequential (`await` one at a time), not concurrent.
- No print() — Rich console or logging only
- Structured logging via structlog (JSON in production)
- Google-style docstrings on all public APIs
- Absolute imports only
- pytest with fixtures, parametrize, no unittest.TestCase
- No file > 500 lines, no function > 50 lines
- Every dependency must justify its inclusion
