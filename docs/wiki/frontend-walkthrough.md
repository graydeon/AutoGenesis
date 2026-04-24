# Frontend Walkthrough

**Owner:** `frontend-engineer`
**Audience:** New hires and engineers touching operator-facing flows
**Status:** Active
**Last updated:** 2026-04-24

AutoGenesis is **CLI-first** today, with a checked-in Textual TUI (`autogenesis tui`) for command-center workflows. There is still no checked-in React/web frontend. Frontend ownership here is still real: we own how operators enter the system, understand state, recover from failures, and move through approval-heavy workflows without confusion.

## Frontend Stack Today

| Surface | Tech | Where it lives | What it owns |
|---|---|---|---|
| Command shell | Typer | `packages/cli/src/autogenesis_cli/app.py`, `commands/*.py` | Command structure, help text, argument ergonomics, and workflow entry points |
| Terminal rendering | Rich | `packages/cli/src/autogenesis_cli/display.py`, `live_display.py` | Streaming text, tool call previews, approval prompts, tables, and live orchestration feedback |
| TUI command center | Textual | `packages/tui/src/autogenesis_tui/` | Roster navigation, live streams, goals/tokens panel, theme picker |
| Documentation UX | Markdown docs | `README.md`, `HANDOFF.md`, `docs/wiki/*` | Onboarding, discoverability, operator confidence, and recovery guidance |
| Auth/browser handoff | Codex CLI login today; host PKCE flow in design docs | `packages/cli/src/autogenesis_cli/commands/login.py` | Browser-based auth and the main browser jump in the core product flow |
| Human approval surface | Twitter queue panel (external dashboard or custom UI) | `docs/wiki/twitter-agent.md`, `docs/wiki/troubleshooting.md` | Review, edit, approve, or reject queued public posts |
| Durable UI state | SQLite + markdown + config | `.autogenesis/`, `$XDG_STATE_HOME`, `.autogenesis/config.yaml` | Inspectable plans, queues, memory, inboxes, config, and status |

> There is **no checked-in React/TypeScript app in this repo yet**. If a web surface is added later, it should wrap the existing CLI/TUI boundaries instead of inventing a parallel source of truth.

## Preferred Direction for Future GUI Work

When we do build a first-class GUI, the default stack should be:

- **React + TypeScript** for route-level screens, typed view models, and reusable UI primitives
- **Modern co-located CSS** with accessibility-first component styling and minimal global leakage
- **Thin data adapters** over existing services and state stores so business logic stays in shared managers, not UI components

## User Experience Principles

1. **CLI-first and headless-safe.** Every critical workflow should remain usable over terminal/SSH.
2. **Fast feedback while work is happening.** Stream output, show progress, and make long-running work feel alive.
3. **Inspectable over magical.** Users should be able to find the plan file, queue entry, config, or DB-backed state behind the UI.
4. **Explicit approval for risky actions.** Public posting, writes, and privileged behavior should feel deliberate.
5. **Consistent nouns across surfaces.** “Goal,” “task,” “employee,” “queue,” and “plan” should mean the same thing in commands, docs, and any future UI.
6. **Recovery is part of the UX.** Status commands, troubleshooting notes, and visible next steps matter as much as the happy path.

## Component Architecture

| Layer | Current implementation | Frontend guidance |
|---|---|---|
| App shell / routing | `autogenesis_cli/app.py` | Keep entry points grouped by real product domains (`ceo`, `hr`, `twitter`, `union`) |
| Workflow controllers | `commands/ceo.py`, `run.py`, `chat.py`, `twitter.py`, etc. | Commands should orchestrate dependencies and user flow, not contain deep business logic |
| Presentation primitives | `display.py`, `live_display.py` | Centralize rendering patterns such as truncation, approvals, tables, and live status |
| Domain services | `packages/core`, `packages/employees`, `packages/twitter` | Put behavior in services/managers so UI layers stay thin |
| Durable state | SQLite stores, markdown plans, config files | Reuse existing sources of truth instead of creating shadow UI state |
| External approval UI | Dashboard integration (bring your own) | Keep dashboards presentational and state-aware, not logic-heavy |

If a React UI lands later, the same layering should hold: **app shell → workflow screen/container → typed hooks/adapters → small presentational components**.

## Main Development Workflows for UI Work

### 1. Changing a CLI flow

1. Start from the operator journey and the exact command path.
2. Update the relevant `commands/*.py` module and shared display helpers.
3. Prefer a reusable display/presenter change over one-off inline `console.print()` calls.
4. Smoke-test the command help and the smallest real workflow path.
5. Run targeted CLI tests plus any affected package tests.

### 2. Changing approvals or dashboards

1. Confirm the real source of truth first (`QueueManager`, config, plan markdown, or another manager).
2. Change the backend/state contract before changing the visual surface when behavior changes.
3. Keep the UI thin; do not duplicate scheduler, queue, or approval rules in multiple places.
4. Validate the whole state transition, not just the screen: pending → approved/rejected/edited → posted.

### 3. Shipping UX changes responsibly

1. Update docs when names, commands, or workflows change.
2. Add or extend troubleshooting guidance for new failure modes.
3. Preserve headless parity unless a browser-only step is unavoidable.
4. Call out any UX regression risk, especially around approval boundaries and operator trust.

## Start Here in Code

- `packages/cli/src/autogenesis_cli/app.py`
- `packages/cli/src/autogenesis_cli/commands/ceo.py`
- `packages/cli/src/autogenesis_cli/commands/run.py`
- `packages/cli/src/autogenesis_cli/commands/twitter.py`
- `packages/cli/src/autogenesis_cli/display.py`
- `packages/cli/src/autogenesis_cli/live_display.py`
- `docs/wiki/twitter-agent.md`
- `docs/wiki/troubleshooting.md`
