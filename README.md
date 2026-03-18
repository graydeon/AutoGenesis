# AutoGenesis

**The token-efficient agent framework. CLI-first. Self-improving. Every token counts.**

[![CI](https://github.com/graydeon/AutoGenesis/actions/workflows/ci.yml/badge.svg)](https://github.com/graydeon/AutoGenesis/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Install

```bash
pip install autogenesis
# or
uv pip install autogenesis
```

For development:

```bash
git clone https://github.com/graydeon/AutoGenesis.git
cd AutoGenesis
./scripts/dev-setup.sh  # installs deps, pre-commit hooks, verifies env
```

Requires Python 3.11+.

## Quick Start

```bash
# Initialize in a project
autogenesis init

# Interactive chat
autogenesis chat

# Single task (pipe-friendly)
autogenesis run "describe this project"
echo "fix the bug in main.py" | autogenesis run

# Configuration
autogenesis config show
autogenesis config get models.default_tier
```

## What It Does

AutoGenesis is an agent framework that treats token efficiency as a first-class concern. It routes requests across model tiers, only loads the tools the model actually needs, caches identical requests, compresses old context, and enforces hard budget limits — all while self-improving its own prompts with constitutional safety guarantees.

### Model Routing

Three tiers with automatic fallback chains:

| Tier | Models | Use Case |
|------|--------|----------|
| **fast** | GPT-4o-mini, Haiku | Simple tasks, classification |
| **standard** | Sonnet, GPT-4o | General coding, analysis |
| **premium** | Opus, o3 | Complex reasoning, architecture |

```bash
autogenesis run --tier fast "what time is it"
autogenesis chat --tier premium
```

### Token Efficiency

- **Progressive tool disclosure** — only load tool definitions the model needs (saves ~2500 tokens/call)
- **Exact-match caching** — SQLite-backed, skip redundant API calls
- **Context compression** — truncate old tool outputs, 30%+ reduction on long conversations
- **Budget enforcement** — session, daily, and monthly cost limits with 80% warnings

### 12 Built-in Tools

`bash`, `file_read`, `file_write`, `file_edit`, `glob`, `grep`, `list_dir`, `think`, `ask_user`, `web_fetch`, `mcp_call`, `sub_agent`

Tools are loaded progressively based on token budget and usage frequency. Hidden tools (`web_fetch`, `sub_agent`) are excluded from context by default.

### Self-Improving Prompts

The optimizer generates candidate prompt variations, evaluates them against golden test suites, and promotes improvements — but a constitutional safety layer ensures optimizations never violate core rules.

```bash
autogenesis optimize run    # generate and evaluate candidates
autogenesis optimize check  # check for quality drift
```

### Security

- **Input guardrails** — prompt injection detection (5+ patterns), dangerous command blocking
- **Output guardrails** — PII detection (SSN, credit card, email), URL exfiltration
- **Audit logging** — append-only JSON Lines with SHA-256 hash chain
- **Adversarial scanning** — built-in self-pentesting suite

```bash
autogenesis scan  # run adversarial probes against your config
```

### MCP Support

Connect to external MCP servers or expose AutoGenesis as one:

```yaml
# .autogenesis/config.yaml
mcp:
  servers:
    my-server:
      command: node
      args: [server.js]
  allowlist:
    - my-server
```

### Plugins

Extend with custom tools via the plugin interface:

```python
from autogenesis_plugins.interface import Plugin, PluginManifest

class MyPlugin(Plugin):
    @property
    def manifest(self):
        return PluginManifest(name="my-plugin", version="1.0.0")
    def get_tools(self):
        return [MyCustomTool()]
```

## Configuration

AutoGenesis uses a 6-layer config cascade (later overrides earlier):

1. Built-in defaults
2. System config: `/etc/autogenesis/config.yaml`
3. User config: `$XDG_CONFIG_HOME/autogenesis/config.yaml`
4. Project config: `.autogenesis/config.yaml`
5. Environment variables: `AUTOGENESIS_MODELS__DEFAULT_TIER=fast`
6. CLI flags: `--tier premium`

```yaml
# .autogenesis/config.yaml
models:
  default_tier: standard
tokens:
  max_cost_per_session: 5.0
  max_cost_per_day: 50.0
security:
  guardrails_enabled: true
```

## Architecture

```
autogenesis/
  packages/
    core/       # Agent loop, models, config, router, events, state
    tools/      # Tool registry, 12 built-in tools, progressive disclosure
    tokens/     # Counting, budgets, caching, compression, reporting
    optimizer/  # Prompt versioning, constitution, evaluation, drift
    security/   # Guardrails, allowlisting, audit, scanner, sandbox
    mcp/        # MCP client + server (FastMCP)
    plugins/    # Plugin interface and loader
    cli/        # Typer + Rich CLI
```

Single-threaded async agent loop. Sequential tool execution. All state is Pydantic V2 models. LiteLLM for provider-agnostic model access.

## Development

```bash
# Run tests
uv run pytest packages/core/tests/ -v

# Run all tests
uv run pytest packages/*/tests/ -v

# Lint
uv run ruff check packages/

# Type check
uv run mypy packages/*/src/

# Format
uv run ruff format packages/
```

Commit messages use [Conventional Commits](https://www.conventionalcommits.org/): `feat(core):`, `fix(tokens):`, `docs:`, etc.

## Roadmap

- **v0.1.0** (current) — Full framework: 8 packages, agent loop, tools, MCP, tokens, optimizer, security, plugins, CLI
- **v0.2.0** — Semantic cache, LLM-based context summarization
- **v0.3.0** — Sub-agent parallelism, multi-agent orchestration
- **v1.0.0** — Stable API, production-ready, external security audit

## Security

Report vulnerabilities via [GitHub Security Advisories](https://github.com/graydeon/AutoGenesis/security/advisories/new). Do not open public issues for security bugs.

## License

[MIT](LICENSE)
