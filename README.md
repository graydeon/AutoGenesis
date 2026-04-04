# AutoGenesis

**Autonomous agent harness powered by OpenAI Codex. Employee-based multi-agent system with persistent memory, inter-agent messaging, CEO orchestration, and a fully custom terminal UI.**

---

## Install

```bash
git clone https://github.com/graydeon/AutoGenesis.git
cd AutoGenesis
uv sync --all-packages   # install all workspace packages
```

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

## Quick Start

```bash
# Login to OpenAI Codex
autogenesis login

# Launch the interactive TUI (recommended)
autogenesis tui

# Or use the CLI directly:

# Give the CEO a goal — it decomposes, assigns, and dispatches
autogenesis ceo run "build user authentication with JWT"

# Or queue individual tasks
autogenesis ceo enqueue "fix the CSS on the login page" --priority 5
autogenesis ceo dispatch

# Check status
autogenesis ceo status

# Manage your team
autogenesis hr list
autogenesis hr hire "Data Engineer"
autogenesis hr train backend-engineer --directive "Always use type hints"

# Run a standup
autogenesis standup

# Start Twitter agent
autogenesis twitter start
```

## TUI — Command Center

`autogenesis tui` launches a three-column terminal interface:

```
┌──────────────────────────────────────────────────────────────────┐
│ ⬡ AutoGenesis   model   ● connected   34,120 tokens              │
├──────────────┬──────────────────────────────┬────────────────────┤
│ EMPLOYEES    │ [ALL] [CEO] [frontend-eng ✕] │ GOALS              │
│              │                              │ ⟳ Add OAuth login  │
│ ● backend    │ CEO › decomposing goal...    │   [████░░░░░░] 2/4 │
│ ▶ frontend   │ frontend-eng › Reading...    │                    │
│ ⟳ analyst   │   ▸ file_read Auth.tsx        │ TOKENS             │
│ ○ devops     │   → 142 lines returned       │ Session: 34,120    │
│              │ frontend-eng › ✓ done        │ Daily:  120,340    │
│ SHORTCUTS    │                              │                    │
│ H S U ?      │                              │                    │
├──────────────┴──────────────────────────────┴────────────────────┤
│ [ CEO ▾ ]  type a message...                              Enter ↵ │
└──────────────────────────────────────────────────────────────────┘
```

**Features:**
- Live streaming agent output from CEO and all employees
- Per-employee stream filtering via filter chips
- Employee detail panel (brain memories, inbox, training directives)
- Token budget meters (session + daily)
- Goal progress tracking
- Three built-in themes: `dracula` (default), `midnight-blue`, `hacker-green`
- Custom themes via TOML files in `~/.config/autogenesis/themes/`
- Full keybindings: `Ctrl+G` new goal · `T` theme cycle · `Esc` deselect · `?` help

```bash
autogenesis tui --theme midnight-blue
```

## How It Works

AutoGenesis models a **software startup** where AI agents are employees:

1. **CEO Orchestrator** decomposes high-level goals into subtasks via LLM reasoning
2. **Employee assignment** — CEO picks the best employee for each subtask (considers tools, training, expertise)
3. **Dispatch** — Each employee runs as a Codex CLI subprocess with a tailored system prompt
4. **Adaptation** — After each subtask, CEO re-evaluates the plan based on results
5. **Retry + escalation** — One retry on failure with context, then escalates to human

### Integrated Systems

| System | Purpose |
|--------|---------|
| **Codex Agent Loop** | OAuth PKCE auth, WebSocket JSON-RPC, tool execution |
| **Employee System** | 9 named roles with brain.db memory, inboxes, changelog, meetings, union |
| **TUI** | Textual-based Command Center: live streaming, employee roster, theme system |
| **Twitter Agent** | Autonomous persona: browse → draft → queue → human approve → post |

## Architecture

```
packages/
  core/        Agent loop, Codex client, auth, config, events, credentials
  employees/   Registry, runtime, brain, inbox, changelog, meetings, union, HR, CEO orchestrator
  tools/       8 built-in tools with progressive disclosure
  tui/         Textual TUI: AppServerManager, CodexWSClient, ThemeManager, 5 widgets
  twitter/     Browser, poster, queue, guardrails, worldview, scheduler, gateway
  cli/         All CLI commands (tui, ceo, hr, twitter, meeting, standup, union)
```

## Documentation

| Doc | What it covers |
|-----|---------------|
| [HANDOFF.md](HANDOFF.md) | Project overview, current state, quick commands |
| [Architecture](docs/wiki/architecture.md) | Package map, key classes, data flow, databases |
| [CLI Reference](docs/wiki/cli-reference.md) | All commands with examples |
| [Employee System](docs/wiki/employee-system.md) | Roles, brain, inbox, HR, meetings, union |
| [CEO Orchestrator](docs/wiki/ceo-orchestrator.md) | Goal decomposition, dispatch, retry, resume |
| [Twitter Agent](docs/wiki/twitter-agent.md) | Browser, queue, gateway, scheduler, guardrails |
| [Configuration](docs/wiki/config.md) | 6-layer cascade, all fields, env vars |
| [Troubleshooting](docs/wiki/troubleshooting.md) | Decision trees for common issues |
| [TUI Design Spec](docs/specs/2026-04-04-autogenesis-tui-design.md) | TUI architecture, widgets, theme system |

## Development

```bash
# Run tests
uv run pytest packages/tui/tests/ packages/core/tests/ packages/employees/tests/ packages/cli/tests/ -q

# Lint + format
uv run ruff check packages/ --fix
uv run ruff format packages/

# Conventional commits
git commit -m "feat(tui): add theme picker"
```

## License

[MIT](LICENSE)
