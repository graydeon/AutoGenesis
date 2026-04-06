# Architecture

## Package Map

```
packages/
  core/        → Agent loop, Codex client, auth, config, events, models, credentials
  employees/   → Registry, runtime, brain, inbox, changelog, meetings, union, HR, orchestrator, state
  tools/       → Tool base, registry, 8 built-in tools, progressive disclosure
  twitter/     → Browser, poster, queue, guardrails, worldview, scheduler, gateway, parser
  cli/         → Typer app, commands: login/logout/run/chat/config/ceo/hr/twitter/meeting/standup/union
  tokens/      → Budget, cache, compression, counter, reporter (v0.1 — not yet wired to Codex)
  optimizer/   → Prompt versioning, constitution, evaluator (v0.1 — not yet wired)
  security/    → Guardrails, allowlist, audit, scanner, sandbox (v0.1 — not yet wired)
  mcp/         → MCP client/server (v0.1 — not yet wired)
  plugins/     → Plugin interface + loader (v0.1 — not yet wired)
```

## Core Data Flow

```
User CLI command
  → CEOOrchestrator.run(goal)
    → CodexClient.create_response_sync() [decompose goal → subtasks]
    → For each subtask:
      → CodexClient.create_response_sync() [assign → employee_id]
      → EmployeeRuntime.build_system_prompt() [brain + inbox + changelog + task]
      → SubAgentManager.spawn() [codex CLI subprocess]
      → Record execution in ceo.db
      → Update plan markdown
      → CodexClient.create_response_sync() [re-evaluate remaining]
    → Return GoalResult
```

## Key Classes

| Class | Package | File | Purpose |
|-------|---------|------|---------|
| `CodexClient` | core | `client.py` | Async OpenAI Responses API via httpx-sse |
| `AgentLoop` | core | `loop.py` | Stream response → parse tool calls → execute → repeat |
| `SubAgentManager` | core | `sub_agents.py` | Spawn codex CLI subprocesses, semaphore-limited |
| `AutoGenesisConfig` | core | `config.py` | 6-layer cascade config (Pydantic) |
| `EventBus` | core | `events.py` | Sync pub/sub, 42 event types |
| `CEOOrchestrator` | employees | `orchestrator.py` | Goal decomposition, assignment, dispatch loop |
| `CEOStateManager` | employees | `state.py` | SQLite CRUD: tasks, goals, executions |
| `EmployeeRegistry` | employees | `registry.py` | Load YAML employee configs (global + project merge) |
| `EmployeeRuntime` | employees | `runtime.py` | Build system prompts, dispatch employees |
| `BrainManager` | employees | `brain.py` | Per-employee SQLite + FTS5 memory |
| `InboxManager` | employees | `inbox.py` | Async inter-employee message queue |
| `ChangelogManager` | employees | `changelog.py` | Append-only markdown team changelog |
| `MeetingManager` | employees | `meetings.py` | Write standup/meeting markdown files |
| `UnionManager` | employees | `union.py` | Proposal filing, voting, resolution |
| `ToolRegistry` | tools | `registry.py` | Progressive disclosure, token-budget filtering |
| `TwitterScheduler` | twitter | `scheduler.py` | Permission gate, active hours, cycle orchestration |
| `QueueManager` | twitter | `queue.py` | SQLite tweet draft queue (pending/approved/posted) |
| `GatewayHandler` | twitter | `gateway.py` | HTTP server signing tweets with real API creds |

## Database Files

| DB | Location | Tables | Owner |
|----|----------|--------|-------|
| `ceo.db` | `.autogenesis/ceo/` | tasks, goals, executions | CEOStateManager |
| `brain.db` | `.autogenesis/employees/{id}/` | memories, memories_fts | BrainManager |
| `inbox.db` | `.autogenesis/employees/{id}/` | messages | InboxManager |
| `union.db` | `$XDG_STATE_HOME/autogenesis/union/{project}/` | proposals, votes | UnionManager |
| `twitter_queue.db` | `$XDG_STATE_HOME/autogenesis/` | queue | QueueManager |

## Config Locations

```
/etc/autogenesis/config.yaml              → System (layer 2)
$XDG_CONFIG_HOME/autogenesis/config.yaml  → User (layer 3)
.autogenesis/config.yaml                  → Project (layer 4)
AUTOGENESIS_* env vars                    → Environment (layer 5, __ separator)
CLI flags                                 → Runtime (layer 6)
```

## Employee YAML Location

```
$XDG_CONFIG_HOME/autogenesis/employees/*.yaml   → Global roster
.autogenesis/employees/*.yaml                   → Project overrides (deep-merged)
```

## Credential Flow

```
Host: stores secrets via environment variables or a secret manager
  → Twitter Gateway (configurable URL): signs API requests
  → Codex OAuth: browser PKCE flow → JWT stored at ~/.local/share/autogenesis/auth.json (0600)
VM/Agent: receives scoped tokens only, never raw API keys
```
