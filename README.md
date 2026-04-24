# AutoGenesis

**Autonomous agent harness powered by OpenAI Codex. Employee-based multi-agent system with persistent memory, inter-agent messaging, a TUI command center, and CEO orchestration.**

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

# Initialize this repo with per-project GitNexus context
autogenesis project init .

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

## How It Works

AutoGenesis models a **software startup** where AI agents are employees:

1. **CEO Orchestrator** decomposes high-level goals into subtasks via LLM reasoning
2. **Employee assignment** — CEO picks the best employee for each subtask (considers tools, training, expertise)
3. **Dispatch** — Each employee runs as a Codex CLI subprocess with a tailored system prompt (plus optional GitNexus per-project code-graph context)
4. **Adaptation** — After each subtask, CEO re-evaluates the plan based on results
5. **Retry + escalation** — One retry on failure with context, then escalates to human

### Integrated Systems

| System | Purpose |
|--------|---------|
| **Codex Agent Loop** | OAuth PKCE auth, SSE streaming, tool execution |
| **Employee System** | 9 named roles with brain.db memory, inboxes, changelog, meetings, union |
| **GitNexus Context Layer** | Auto-index per repository, then inject focused code-flow context to reduce exploratory token spend |
| **Twitter Agent** | Autonomous persona: browse → draft → queue → human approve → post |
| **TUI Command Center** | Textual interface for roster navigation, live streams, goals, token status, and themes |

## Architecture

```
packages/
  core/        Agent loop, Codex client, auth, config, events, credentials
  employees/   Registry, runtime, brain, inbox, changelog, meetings, union, HR, CEO orchestrator
  tools/       8 built-in tools with progressive disclosure
  security/    Guardrails, allowlist, audit logging, scanner, sandbox primitives
  tokens/      Budget, cache, compression, reporter, deferred token counter
  mcp/         MCP client/server/registry
  plugins/     Plugin interface and loader
  tui/         Textual command center
  twitter/     Browser, poster, queue, guardrails, worldview, scheduler, gateway
  cli/         All CLI commands (ceo, hr, twitter, meeting, standup, union)
```

## Documentation

| Doc | What it covers |
|-----|---------------|
| [HANDOFF.md](HANDOFF.md) | Project overview, current state, quick commands |
| [Status Report](docs/wiki/status-report.md) | Current local/GitHub validation, CI state, and next priorities |
| [Security Audit](docs/wiki/security-audit.md) | Security findings, verification results, and hardening roadmap |
| [Architecture](docs/wiki/architecture.md) | Package map, key classes, data flow, databases |
| [CLI Reference](docs/wiki/cli-reference.md) | All commands with examples |
| [Employee System](docs/wiki/employee-system.md) | Roles, brain, inbox, HR, meetings, union |
| [CEO Orchestrator](docs/wiki/ceo-orchestrator.md) | Goal decomposition, dispatch, retry, resume |
| [Twitter Agent](docs/wiki/twitter-agent.md) | Browser, queue, gateway, scheduler, guardrails |
| [Configuration](docs/wiki/config.md) | 6-layer cascade, all fields, env vars |
| [Troubleshooting](docs/wiki/troubleshooting.md) | Decision trees for common issues |

## Development

```bash
# Run the full package test suite (457 passing as of 2026-04-24)
uv run pytest packages/*/tests tests -q --tb=short

# Coverage gate used by CI
uv run pytest packages/*/tests/ -q --tb=short --cov --cov-report=term-missing --cov-fail-under=80

# Lint, format, and type check
uv run ruff check packages/
uv run ruff format --check packages/
uv run mypy packages/

# Security checks
uv run ruff check --select S packages/
uvx pip-audit

# Conventional commits
git commit -m "feat(ceo): add goal decomposition"
```

Current status: tests, coverage, full Ruff lint, strict mypy, security lint, dependency audit, and package builds pass locally. See the [Status Report](docs/wiki/status-report.md).

## License

[MIT](LICENSE)
