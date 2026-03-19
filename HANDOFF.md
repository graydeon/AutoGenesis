# AutoGenesis — Handoff Document

> Read this first when picking up the project. Points to wiki docs for details.

## What This Is

Autonomous agent harness powered by OpenAI Codex CLI. Three integrated systems:

1. **Codex Agent Loop** — OAuth PKCE auth, SSE streaming via Responses API, tool execution
2. **Agent Employee System** — Named subagents (9 roles) with persistent memory, inboxes, changelog, meetings, labor union
3. **CEO Orchestrator** — Decomposes goals into subtasks, assigns to employees via LLM reasoning, dispatches, adapts
4. **Twitter Agent** — Autonomous persona that browses Twitter via Pinchtab, drafts tweets, queues for human approval

## Current State (2026-03-19)

- **223 tests passing** across core/employees/tools/cli
- All packages implemented and wired
- One gap: **live Codex connection** requires real ChatGPT Plus OAuth credentials

## Quick Commands

```bash
uv run autogenesis ceo run "build a landing page"   # Goal decomposition + dispatch
uv run autogenesis ceo enqueue "fix login bug"       # Queue a task
uv run autogenesis ceo dispatch                      # Execute next queued task
uv run autogenesis hr list                           # List employees
uv run autogenesis twitter start                     # Start Twitter scheduler
uv run python -m pytest packages/core/tests/ packages/employees/tests/ packages/tools/tests/ packages/cli/tests/ -v
```

## Documentation Map

| Doc | What it covers |
|-----|---------------|
| `docs/wiki/architecture.md` | Package map, key classes, data flow |
| `docs/wiki/cli-reference.md` | All CLI commands with examples |
| `docs/wiki/employee-system.md` | Employee roles, brain, inbox, HR ops |
| `docs/wiki/ceo-orchestrator.md` | Goal decomposition, dispatch, retry |
| `docs/wiki/twitter-agent.md` | Browser, queue, gateway, scheduler |
| `docs/wiki/troubleshooting.md` | Decision tree for common issues |
| `docs/wiki/config.md` | 6-layer config cascade, all fields |

## Key Architectural Decisions

- **Codex CLI as subprocess** — SubAgentManager spawns `codex --quiet --full-auto` with system prompt file
- **No LiteLLM** — Direct OpenAI Responses API via httpx-sse
- **SQLite everywhere** — brain.db, inbox.db, ceo.db, union.db, twitter_queue.db (all via aiosqlite)
- **Markdown plans** — CEO writes human-readable plan files, updates checkboxes as work completes
- **Gateway pattern** — Host holds secrets, VM gets scoped tokens. Twitter gateway at localhost:1456
- **No autonomous posting** — All tweets queue for human approval via infra-dashboard panel
