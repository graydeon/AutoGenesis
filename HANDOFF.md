# AutoGenesis — Handoff Document

> Read this first when picking up the project. Points to wiki docs for details.

## What This Is

Autonomous agent harness powered by OpenAI Codex CLI. Four integrated systems:

1. **Codex Agent Loop** — OAuth PKCE auth, SSE streaming via Responses API, tool execution
2. **Agent Employee System** — Named subagents (9 roles) with persistent memory, inboxes, changelog, meetings, labor union
3. **CEO Orchestrator** — Decomposes goals into subtasks, assigns to employees via LLM reasoning, dispatches, adapts
4. **Twitter Agent** — Autonomous persona that browses Twitter via Pinchtab, drafts tweets, queues for human approval
5. **TUI** — Textual-based Command Center (`autogenesis tui`): 3-column layout with live roster, streaming agent output, goals/tokens panel, theme picker

## Current State (2026-04-04)

- **35 TUI tests passing** in `packages/tui/`; other package tests intact
- TUI implemented and wired: `packages/tui/` fully functional, `autogenesis tui` CLI command live
- One gap: **live Codex connection** requires real ChatGPT Plus OAuth credentials (codex app-server needs `~/.codex/` auth)

## TUI — Known State

The TUI was just implemented and bug-fixed. Five issues were resolved (commit `3da1afb`):
- Disconnected: was passing invalid `--dangerously-bypass-approvals-and-sandbox` to `codex app-server`; fixed with `-c approval_policy="never"`
- Right panel empty: `RightPanel` didn't call `_refresh()` on mount; fixed with `on_mount()`
- Roster not clickable: added `on_key()` (↑/↓/Enter) and `on_click()` handlers
- Dropdown not working: added `on_static_click()` to `InputBar` so clicking `[ CEO ▾ ]` cycles targets
- Column borders missing: added `border-right`/`border-left` CSS to visually separate columns

**Outstanding unstaged changes** (not yet committed): Several files from the feature/tui branch merge are unstaged but present in the working tree — `.gitignore`, `HANDOFF.md`, `README.md`, wiki docs, `packages/cli/`, `packages/core/sub_agents.py`, `packages/employees/`. These represent the remainder of the feature/tui merge that got staged but wasn't committed in the last session. They need a separate review and commit.

## Quick Commands

```bash
uv run autogenesis tui                               # Launch Command Center TUI
uv run autogenesis tui --theme hacker-green          # Launch with specific theme
uv run autogenesis ceo run "build a landing page"   # Goal decomposition + dispatch
uv run autogenesis ceo enqueue "fix login bug"       # Queue a task
uv run autogenesis ceo dispatch                      # Execute next queued task
uv run autogenesis hr list                           # List employees
uv run autogenesis twitter start                     # Start Twitter scheduler
uv run python -m pytest packages/core/tests/ packages/employees/tests/ packages/tools/tests/ packages/cli/tests/ -v
uv run --package autogenesis-tui pytest packages/tui/tests/ -v   # TUI tests only
```

## Documentation Map

| Doc | What it covers |
|-----|---------------|
| `docs/wiki/architecture.md` | Package map, key classes, data flow |
| `docs/wiki/cli-reference.md` | All CLI commands with examples |
| `docs/wiki/employee-system.md` | Employee roles, brain, inbox, HR ops |
| `docs/wiki/backend-walkthrough.md` | Backend services, APIs, databases, and reliability watch-outs |
| `docs/wiki/onboarding-packet.md` | Published onboarding hub with orientation snapshot, agenda, day-one checklists, norms, and key links |
| `docs/wiki/onboarding-plan.md` | Employee onboarding roster, checklist, pre-work, and agenda |
| `docs/wiki/security-onboarding-module.md` | Mandatory security baseline for accounts, secrets, access, incident reporting, and collaboration |
| `docs/wiki/onboarding-orientation-runbook.md` | Live orientation script, owner handoffs, intro order, and blocker capture plan |
| `docs/wiki/cto-orientation-segment.md` | Mission, product architecture, team interfaces, standards, and technical priorities |
| `docs/wiki/ceo-orchestrator.md` | Goal decomposition, dispatch, retry |
| `docs/wiki/twitter-agent.md` | Browser, queue, gateway, scheduler |
| `docs/wiki/troubleshooting.md` | Decision tree for common issues |
| `docs/wiki/config.md` | 6-layer config cascade, all fields |

## Key Architectural Decisions

- **Codex CLI as subprocess** — SubAgentManager spawns `codex --quiet --full-auto` with system prompt file
- **No LiteLLM** — Direct OpenAI Responses API via httpx-sse
- **SQLite everywhere** — brain.db, inbox.db, ceo.db, union.db, twitter_queue.db (all via aiosqlite)
- **Markdown plans** — CEO writes human-readable plan files, updates checkboxes as work completes
- **Gateway pattern** — Host holds secrets, VM gets scoped tokens. Twitter gateway URL is configurable
- **No autonomous posting** — All tweets queue for human approval before posting
