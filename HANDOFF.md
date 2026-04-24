# AutoGenesis — Handoff Document

> Read this first when picking up the project. Updated: 2026-04-24 (repository review and security audit)

## What This Is

Autonomous agent harness powered by OpenAI Codex CLI. Five integrated systems:

1. **Codex Agent Loop** — OAuth PKCE auth, SSE streaming via Responses API, tool execution
2. **Agent Employee System** — Named subagents (9 roles) with persistent memory, inboxes, changelog, meetings, labor union
3. **CEO Orchestrator** — Decomposes goals into subtasks, assigns to employees via LLM reasoning, dispatches, adapts
4. **Twitter Agent** — Autonomous persona that browses Twitter via Pinchtab, drafts tweets, queues for human approval
5. **TUI** — Textual-based Command Center (`autogenesis tui`): 3-column layout with live roster, streaming agent output, goals/tokens panel, theme picker

## Current State (2026-04-24 Review)

### Verified Locally
- **457 tests passing** on Python 3.13.12
- **Coverage passes** the CI threshold: 86.65% total coverage
- **Full Ruff lint passes** with `uv run ruff check packages/`
- **Strict mypy passes** with `uv run mypy packages/`
- **Package builds pass** with `uv build --all-packages`
- **Security lint passes** with `uv run ruff check --select S packages/`
- **Dependency audit passes** with `uvx pip-audit` reporting no known vulnerabilities
- **GitNexus index refreshed**: 4,156 symbols, 8,842 relationships, 225 flows

### Current Failures / Gaps
- **GitHub Nightly is still failing on remote `origin/main`** as of 2026-04-24 because these fixes are not pushed yet.
- **Remote GitHub branch is behind local**: `origin/main` is `7fa9858`, local `main` is `92b39c0`.
- **Token counting is still deferred** in the Codex integration.
- **Guardrails and audit logging are not universal** across all execution paths yet.

### Recent TUI Work
- **TUI keyboard navigation** — Full roster control without mouse:
  - ↑/↓: Single row navigation
  - PGUP/PGDOWN or Ctrl+B/Ctrl+F: Jump 5 rows
  - HOME: Jump to CEO (first item)
  - END: Jump to last employee
  - ENTER: Select/deselect employee
  - ESCAPE: Exit input box, focus screen
  - TAB: Cycle focus to roster
- **CEO in roster** — CEO Orchestrator now appears as first item with "active" status
- **GitNexus integration** — Task-specific code context injection for employees
- **Project init command** — `autogenesis project init` for per-project GitNexus setup
- **Twitter gateway** — Credential-isolated tweet posting via HTTP gateway with required auth by default and aligned poster/gateway response schema

### ⚠️ Known Limitations
- **Live Codex connection** requires real ChatGPT Plus OAuth credentials (TUI shows "disconnected" without them)
- **Token counting is not fully ported** to the Codex integration yet
- **Security guardrails and audit logs are not fully wired** into every tool/public-action path

## Quick Start

```bash
# 1. Install dependencies
uv sync --all-packages --extra dev

# 2. Verify tests
uv run pytest packages/*/tests tests -q --tb=short  # Should show 457 passed

# 3. Initialize project (first time only)
uv run autogenesis project init .

# 4. Launch TUI
uv run autogenesis tui                    # Default theme
uv run autogenesis tui --theme dracula    # Dark theme
```

## TUI Navigation Guide

### Input Box Focus
| Key | Action |
|-----|--------|
| ENTER | Send message to selected target |
| ESCAPE | Defocus/blur input (focus to screen) |
| TAB | Cycle focus to roster |
| Ctrl+SPACE | Cycle target (CEO → employees) |

### Roster Navigation (after leaving input)
| Key | Action |
|-----|--------|
| ↑ / ↓ | Previous/next employee |
| PGUP / Ctrl+B | Jump back 5 rows |
| PGDOWN / Ctrl+F | Jump forward 5 rows |
| HOME | Jump to CEO (top of list) |
| END | Jump to last employee |
| ENTER | Select employee / show details in right panel |
| H | Show HR panel (hire/train employees) |
| S | Standup report |
| U | Labor union panel |
| ? | Help overlay |

### Global Shortcuts
| Key | Action |
|-----|--------|
| Ctrl+C or Q | Quit TUI |
| Ctrl+T | Toggle theme picker |

## GitNexus Integration

GitNexusContextProvider (`packages/employees/src/autogenesis_employees/gitnexus.py`):
- Auto-indexes repos on first use
- Queries GitNexus for task-relevant code context
- Caches results per (repo, task) tuple
- Injects context into employee prompts for token-efficient code understanding

Usage:
```bash
autogenesis project init .              # Initialize GitNexus for current project
autogenesis project init . --force-index  # Force re-index
```

## CLI Commands

```bash
# TUI
uv run autogenesis tui                               # Launch Command Center
uv run autogenesis tui --theme hacker-green          # With theme

# CEO / Task Management
uv run autogenesis ceo run "build a landing page"     # Goal decomposition + dispatch
uv run autogenesis ceo enqueue "fix login bug"        # Queue a task
uv run autogenesis ceo dispatch                       # Execute next queued task
uv run autogenesis ceo status                         # Check current status

# HR / Employees
uv run autogenesis hr list                            # List all employees
uv run autogenesis hr hire "Backend Engineer"          # Hire new employee
uv run autogenesis hr train <id> --directive "Always use type hints"

# Twitter (optional)
uv run autogenesis twitter start                      # Start Twitter scheduler
uv run python -m autogenesis_twitter.gateway --gateway-token <token>

# Testing
uv run python -m pytest packages/ -q                  # All tests
uv run python -m pytest packages/tui/tests/ -q        # TUI only
uv run python -m pytest packages/employees/tests/ -q # Employees only
```

## Documentation Map

| Doc | What it covers |
|-----|---------------|
| `docs/wiki/architecture.md` | Package map, key classes, data flow |
| `docs/wiki/status-report.md` | Current validation, CI state, GitHub state, next priorities |
| `docs/wiki/security-audit.md` | Security findings and hardening roadmap |
| `docs/wiki/cli-reference.md` | All CLI commands with examples |
| `docs/wiki/employee-system.md` | Employee roles, brain, inbox, HR ops |
| `docs/wiki/backend-walkthrough.md` | Backend services, APIs, databases |
| `docs/wiki/ceo-orchestrator.md` | Goal decomposition, dispatch, retry |
| `docs/wiki/twitter-agent.md` | Browser, queue, gateway, scheduler |
| `docs/wiki/config.md` | 6-layer config cascade, all fields |
| `docs/wiki/troubleshooting.md` | Decision tree for common issues |
| `docs/wiki/onboarding-packet.md` | New dev onboarding hub |

## Key Files

| File | Purpose |
|------|---------|
| `packages/tui/src/autogenesis_tui/app.py` | Main TUI application |
| `packages/tui/src/autogenesis_tui/widgets/roster.py` | Employee roster widget (keyboard nav) |
| `packages/tui/src/autogenesis_tui/widgets/input_bar.py` | Input box with target selector |
| `packages/employees/src/autogenesis_employees/orchestrator.py` | CEO orchestration logic |
| `packages/employees/src/autogenesis_employees/gitnexus.py` | GitNexus context provider |
| `packages/cli/src/autogenesis_cli/commands/ceo.py` | CLI commands for CEO |
| `pyproject.toml` | Workspace configuration |

## Recent Commits (This Session)

- `7fa9858` — style(lint): Fix all pre-existing lint issues across codebase
- `ac5ae03` — fix(tui): Correct click offset in employee roster
- `56b4168` — feat(tui): Add keyboard navigation and CEO to roster
- `70a2cf9` — feat(tui): Add Escape/Tab to exit input box and focus roster

## Key Architectural Decisions

- **Codex CLI as subprocess** — SubAgentManager spawns `codex exec` with a system prompt file; defaults are now `approval_policy="on-request"` and `sandbox_mode="workspace-write"`, with unsafe bypass available only by explicit opt-in
- **No LiteLLM** — Direct OpenAI Responses API via httpx-sse
- **SQLite everywhere** — brain.db, inbox.db, ceo.db, union.db, twitter_queue.db (all via aiosqlite)
- **Markdown plans** — CEO writes human-readable plan files, updates checkboxes as work completes
- **Gateway pattern** — Host holds secrets, VM gets scoped tokens. Twitter gateway URL is configurable
- **No autonomous posting** — All tweets queue for human approval before posting
- **Keyboard-first TUI** — Mouse support secondary due to terminal emulator variance

## Next Steps / Open Items

1. **Push/reconcile CI fixes** — Get remote Nightly green from the local passing state.
2. **Wire token counting** — Make token efficiency measurable with real Codex/Responses usage.
3. **Finish guardrail integration** — Enforce prompt/output guardrails at intake, tool approval, external-content, and public-action boundaries.
4. **Expand audit logging** — Emit redacted policy/tool/public-action audit events consistently.
5. **Add supply-chain controls** — Dependabot, dependency review, CodeQL/Scorecard, and release attestations.

---

*Last updated: 2026-04-24. For questions, check `docs/wiki/status-report.md`, `docs/wiki/security-audit.md`, and `docs/wiki/troubleshooting.md` first.*
