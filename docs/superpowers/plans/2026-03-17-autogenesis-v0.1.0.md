# AutoGenesis v0.1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build AutoGenesis from zero to v0.1.0 — a CLI-first, token-efficient, self-improving agentic workflow framework with 8 Python packages.

**Architecture:** 8-package uv workspace monorepo. Single-threaded async agent loop (Claude Code pattern). 3-tier model routing via LiteLLM. Progressive tool disclosure for token efficiency. MCP client+server from day one. Constitutional safety layer for self-improving prompts.

**Tech Stack:** Python 3.11+, Typer, Rich, Pydantic V2, LiteLLM, FastMCP, structlog, pytest, ruff, mypy, uv

**Spec:** `docs/superpowers/specs/2026-03-17-autogenesis-design.md`

---

## Parallel Execution Model

Tasks within each phase that share the same parallelism group can be dispatched simultaneously. Tasks with `DEPENDS_ON` must wait for their dependencies to complete. Quality gates block phase transitions.

---

## Phase 1: Scaffolding & Infrastructure

All Phase 1 tasks run in parallel. No application code — structure only.

### Task 1A: Monorepo Skeleton

**Parallel group:** Phase 1
**DEPENDS_ON:** none

**Files:**
- Create: `pyproject.toml` (root workspace)
- Create: `packages/core/pyproject.toml`
- Create: `packages/core/src/autogenesis_core/__init__.py`
- Create: `packages/core/src/autogenesis_core/loop.py` (empty)
- Create: `packages/core/src/autogenesis_core/state.py` (empty)
- Create: `packages/core/src/autogenesis_core/models.py` (empty)
- Create: `packages/core/src/autogenesis_core/config.py` (empty)
- Create: `packages/core/src/autogenesis_core/context.py` (empty)
- Create: `packages/core/src/autogenesis_core/router.py` (empty)
- Create: `packages/core/src/autogenesis_core/events.py` (empty)
- Create: `packages/core/src/autogenesis_core/sandbox.py` (empty)
- Create: `packages/core/tests/__init__.py`
- Create: `packages/tools/pyproject.toml`
- Create: `packages/tools/src/autogenesis_tools/__init__.py`
- Create: `packages/tools/src/autogenesis_tools/registry.py` (empty)
- Create: `packages/tools/src/autogenesis_tools/bash.py` (empty)
- Create: `packages/tools/src/autogenesis_tools/filesystem.py` (empty)
- Create: `packages/tools/src/autogenesis_tools/base.py` (empty)
- Create: `packages/tools/tests/__init__.py`
- Create: `packages/tokens/pyproject.toml`
- Create: `packages/tokens/src/autogenesis_tokens/__init__.py`
- Create: `packages/tokens/src/autogenesis_tokens/counter.py` (empty)
- Create: `packages/tokens/src/autogenesis_tokens/budget.py` (empty)
- Create: `packages/tokens/src/autogenesis_tokens/cache.py` (empty)
- Create: `packages/tokens/src/autogenesis_tokens/compression.py` (empty)
- Create: `packages/tokens/src/autogenesis_tokens/reporter.py` (empty)
- Create: `packages/tokens/tests/__init__.py`
- Create: `packages/optimizer/pyproject.toml`
- Create: `packages/optimizer/src/autogenesis_optimizer/__init__.py`
- Create: `packages/optimizer/src/autogenesis_optimizer/engine.py` (empty)
- Create: `packages/optimizer/src/autogenesis_optimizer/versioning.py` (empty)
- Create: `packages/optimizer/src/autogenesis_optimizer/evaluator.py` (empty)
- Create: `packages/optimizer/src/autogenesis_optimizer/constitution.py` (empty)
- Create: `packages/optimizer/src/autogenesis_optimizer/drift.py` (empty)
- Create: `packages/optimizer/tests/__init__.py`
- Create: `packages/security/pyproject.toml`
- Create: `packages/security/src/autogenesis_security/__init__.py`
- Create: `packages/security/src/autogenesis_security/guardrails.py` (empty)
- Create: `packages/security/src/autogenesis_security/sandbox.py` (empty)
- Create: `packages/security/src/autogenesis_security/audit.py` (empty)
- Create: `packages/security/src/autogenesis_security/scanner.py` (empty)
- Create: `packages/security/src/autogenesis_security/allowlist.py` (empty)
- Create: `packages/security/tests/__init__.py`
- Create: `packages/mcp/pyproject.toml`
- Create: `packages/mcp/src/autogenesis_mcp/__init__.py`
- Create: `packages/mcp/src/autogenesis_mcp/client.py` (empty)
- Create: `packages/mcp/src/autogenesis_mcp/server.py` (empty)
- Create: `packages/mcp/src/autogenesis_mcp/registry.py` (empty)
- Create: `packages/mcp/tests/__init__.py`
- Create: `packages/plugins/pyproject.toml`
- Create: `packages/plugins/src/autogenesis_plugins/__init__.py`
- Create: `packages/plugins/src/autogenesis_plugins/interface.py` (empty)
- Create: `packages/plugins/src/autogenesis_plugins/loader.py` (empty)
- Create: `packages/plugins/src/autogenesis_plugins/builtin/__init__.py`
- Create: `packages/plugins/tests/__init__.py`
- Create: `packages/cli/pyproject.toml`
- Create: `packages/cli/src/autogenesis_cli/__init__.py`
- Create: `packages/cli/src/autogenesis_cli/app.py` (empty)
- Create: `packages/cli/src/autogenesis_cli/commands/__init__.py`
- Create: `packages/cli/src/autogenesis_cli/commands/chat.py` (empty)
- Create: `packages/cli/src/autogenesis_cli/commands/run.py` (empty)
- Create: `packages/cli/src/autogenesis_cli/commands/init.py` (empty)
- Create: `packages/cli/src/autogenesis_cli/commands/config.py` (empty)
- Create: `packages/cli/src/autogenesis_cli/commands/optimize.py` (empty)
- Create: `packages/cli/src/autogenesis_cli/commands/scan.py` (empty)
- Create: `packages/cli/src/autogenesis_cli/commands/tokens.py` (empty)
- Create: `packages/cli/src/autogenesis_cli/commands/plugins.py` (empty)
- Create: `packages/cli/src/autogenesis_cli/commands/mcp_cmd.py` (empty)
- Create: `packages/cli/src/autogenesis_cli/commands/audit.py` (empty)
- Create: `packages/cli/src/autogenesis_cli/display.py` (empty)
- Create: `packages/cli/src/autogenesis_cli/completions.py` (empty)
- Create: `packages/cli/tests/__init__.py`
- Create: `prompts/system/core.yaml` (placeholder)
- Create: `prompts/system/constitution.yaml` (placeholder)
- Create: `prompts/tools/definitions.yaml` (placeholder)
- Create: `prompts/tests/` (golden test suite directory)
- Create: `prompts/manifest.yaml` (version tracking manifest)
- Create: `prompts/README.md`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py` (empty)
- Create: `tests/integration/__init__.py`
- Create: `tests/e2e/__init__.py`
- Create: `.autogenesis/config.yaml` (placeholder)
- Create: `.gitignore`

- [ ] **Step 1: Create root pyproject.toml**

```toml
[project]
name = "autogenesis"
version = "0.1.0"
description = "The token-efficient agent framework. CLI-first. Self-improving. Every token counts."
requires-python = ">=3.11"
license = "MIT"
readme = "README.md"

[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
autogenesis-core = { workspace = true }
autogenesis-tools = { workspace = true }
autogenesis-tokens = { workspace = true }
autogenesis-optimizer = { workspace = true }
autogenesis-security = { workspace = true }
autogenesis-mcp = { workspace = true }
autogenesis-plugins = { workspace = true }
autogenesis-cli = { workspace = true }

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["ALL"]
ignore = [
    "D1",      # missing docstrings (early dev)
    "ANN1",    # missing type annotations for self/cls
    "COM812",  # trailing comma (conflicts with formatter)
    "ISC001",  # implicit string concat (conflicts with formatter)
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "D", "ANN"]
"**/tests/**/*.py" = ["S101", "D", "ANN"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["packages/*/tests", "tests"]
asyncio_mode = "auto"
markers = [
    "e2e: end-to-end tests requiring real LLM API keys",
]
```

- [ ] **Step 2: Create core package pyproject.toml**

```toml
# packages/core/pyproject.toml
[project]
name = "autogenesis-core"
version = "0.1.0"
description = "AutoGenesis core runtime: agent loop, state, models, config, events"
requires-python = ">=3.11"
license = "MIT"
dependencies = [
    "pydantic>=2.0,<3.0",
    "pydantic-settings>=2.0,<3.0",
    "pyyaml>=6.0,<7.0",
    "structlog>=24.0",
    "litellm>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-cov>=5.0",
    "ruff>=0.8",
    "mypy>=1.13",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/autogenesis_core"]
```

- [ ] **Step 3: Create remaining 7 package pyproject.toml files**

Each follows the same pattern as core. Key dependency differences:

**tools:** depends on `autogenesis-core`, `autogenesis-mcp`
**tokens:** depends on `autogenesis-core`, `litellm>=1.0`
**optimizer:** depends on `autogenesis-core`, `autogenesis-tokens`
**security:** depends on `autogenesis-core`
**mcp:** depends on `autogenesis-core`, `mcp>=1.0`, `fastmcp>=0.1`
**plugins:** depends on `autogenesis-core`, `autogenesis-tools`
**cli:** depends on all 7 packages plus `typer>=0.12`, `rich>=13.0`

The cli package additionally defines:
```toml
[project.scripts]
autogenesis = "autogenesis_cli.app:main"
```

- [ ] **Step 4: Create all __init__.py files and empty module files**

Every `__init__.py` exports the package version:
```python
"""AutoGenesis core runtime."""

__version__ = "0.1.0"
```

All `.py` module files are empty except for a module docstring:
```python
"""Module description from spec."""
```

- [ ] **Step 5: Create directory structure for prompts, tests, scripts, examples, docs**

```
prompts/system/core.yaml         → "version: '1.0.0'\ncontent: ''"
prompts/system/constitution.yaml → initial constitutional rules from spec
prompts/tools/definitions.yaml   → "tools: []"
prompts/tests/                   → create directory with sample golden test:
  prompts/tests/hello_world.yaml → {input: "Say hello", expected_contains: "hello", metrics: {task_completion: 5}}
prompts/manifest.yaml            → initial manifest per spec schema:
  {prompts: {core: {active_version: "1.0.0", active_environment: "dev", versions: {"1.0.0": {checksum: "<computed>", created_at: "<now>"}}}}}
prompts/README.md                → "# Prompt Templates\nVersion-controlled prompt templates."
tests/__init__.py                → empty
tests/conftest.py                → "# Shared fixtures defined in Phase 2"
tests/integration/__init__.py    → empty
tests/e2e/__init__.py            → empty
examples/                        → create directory only
docs/docs/                       → create directory only
scripts/                         → create directory only
.autogenesis/config.yaml         → "# AutoGenesis dogfooding config"
```

- [ ] **Step 6: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
*.egg

# Virtual environments
.venv/
venv/

# uv
.uv/

# Environment
.env
.env.*

# IDE
.idea/
.vscode/
*.swp
*.swo

# AutoGenesis
.autogenesis/secrets/

# Testing
.coverage
htmlcov/
.pytest_cache/

# mypy
.mypy_cache/

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 7: Run `uv sync` to verify workspace resolves**

Run: `cd /home/gray/dev/AutoGenesis && uv sync`
Expected: exits 0, creates `.venv/` and `uv.lock`

- [ ] **Step 8: Verify all packages import cleanly**

Run: `uv run python -c "import autogenesis_core; import autogenesis_tools; import autogenesis_tokens; import autogenesis_optimizer; import autogenesis_security; import autogenesis_mcp; import autogenesis_plugins; import autogenesis_cli; print('All imports OK')"`
Expected: "All imports OK"

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat: scaffold 8-package uv workspace monorepo

Create complete directory structure with pyproject.toml for each
package, empty module files, prompts directory, test infrastructure,
and .gitignore. All packages import cleanly via uv sync."
```

---

### Task 1B: Community & Governance Files

**Parallel group:** Phase 1
**DEPENDS_ON:** none

**Files:**
- Create: `README.md`
- Create: `CONTRIBUTING.md`
- Create: `CODE_OF_CONDUCT.md`
- Create: `GOVERNANCE.md`
- Create: `ROADMAP.md`
- Create: `CHANGELOG.md`
- Create: `SECURITY.md`
- Create: `LICENSE`
- Create: `KNOWN_ISSUES.md`

- [ ] **Step 1: Create LICENSE (MIT, 2026)**

```
MIT License

Copyright (c) 2026 AutoGenesis Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
...
```

- [ ] **Step 2: Create README.md**

Must include:
- Project name + tagline: "The token-efficient agent framework. CLI-first. Self-improving. Every token counts."
- Badges: PyPI version, Python versions (3.11+), License (MIT), CI status
- 30-second install: `pipx install autogenesis` or `uv tool install autogenesis`
- "Getting Started in 5 Minutes" quickstart with `autogenesis init`, `autogenesis chat`, `autogenesis run` examples
- Feature highlights (5 pillars) with brief descriptions
- Architecture diagram in Mermaid (master loop → tools → model router → providers)
- Comparison table vs LangChain/CrewAI/AutoGen showing token efficiency focus
- Contributing link, License notice
- "Built in public" section

- [ ] **Step 3: Create CONTRIBUTING.md**

Must include:
- One-command dev setup: `./scripts/dev-setup.sh`
- Branch naming: `feat/`, `fix/`, `docs/`, `security/`
- Commit convention: Conventional Commits
- Code style: ruff format + ruff check, type hints required, Pydantic models
- Test requirements: pytest, 80% coverage for new code
- Prompt contribution guidelines
- Security vulnerability reporting link to SECURITY.md

- [ ] **Step 4: Create CODE_OF_CONDUCT.md**

Contributor Covenant v2.1 — full text.

- [ ] **Step 5: Create GOVERNANCE.md, ROADMAP.md, CHANGELOG.md, SECURITY.md, KNOWN_ISSUES.md**

**GOVERNANCE.md:** BDFL model, RFC process, maintainer graduation path.
**ROADMAP.md:** v0.1.0 through v1.0.0 milestones matching spec roadmap.
**CHANGELOG.md:** Keep a Changelog format, `## [Unreleased]` header.
**SECURITY.md:** Responsible disclosure, 90-day timeline.
**KNOWN_ISSUES.md:** Empty with header `# Known Issues\n\nNone yet.`

- [ ] **Step 6: Commit**

```bash
git add README.md CONTRIBUTING.md CODE_OF_CONDUCT.md GOVERNANCE.md ROADMAP.md CHANGELOG.md SECURITY.md LICENSE KNOWN_ISSUES.md
git commit -m "docs: add community, governance, and legal files"
```

---

### Task 1C: CI/CD Pipeline

**Parallel group:** Phase 1
**DEPENDS_ON:** none

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/nightly.yml`
- Create: `.github/workflows/release.yml`
- Create: `.github/ISSUE_TEMPLATE/bug_report.md`
- Create: `.github/ISSUE_TEMPLATE/feature_request.md`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`

- [ ] **Step 1: Create ci.yml**

5 parallel jobs: `lint-and-format`, `test-unit` (matrix: py 3.11/3.12/3.13), `test-integration`, `security-check`, `build-check`. Pin all action versions to SHA. Cache uv. Coverage gate at 80%.

- [ ] **Step 2: Create nightly.yml**

Cron `0 4 * * *`. All CI jobs plus `prompt-regression` and `token-efficiency-benchmark`. Cost cap via `MAX_NIGHTLY_COST_USD=5.0` env var.

- [ ] **Step 3: Create release.yml**

Release Please action. Conventional Commits → version bump. Build + publish via OIDC trusted publishing.

- [ ] **Step 4: Create issue templates and PR template**

Bug report: structured YAML frontmatter, version/OS/steps sections.
Feature request: problem statement, proposed solution, alternatives.
PR template: description, checklist (tests, docs, no regressions, token impact).

- [ ] **Step 5: Commit**

```bash
git add .github/
git commit -m "ci: add GitHub Actions workflows and templates"
```

---

### Task 1D: Developer Tooling

**Parallel group:** Phase 1
**DEPENDS_ON:** none

**Files:**
- Create: `scripts/dev-setup.sh`
- Create: `.pre-commit-config.yaml`

- [ ] **Step 1: Create scripts/dev-setup.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== AutoGenesis Dev Setup ==="

# Check Python 3.11+
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required="3.11"
if [ "$(printf '%s\n' "$required" "$python_version" | sort -V | head -n1)" != "$required" ]; then
    echo "ERROR: Python 3.11+ required (found $python_version)"
    exit 1
fi

# Check/install uv
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Sync workspace
echo "Syncing workspace..."
uv sync --all-extras

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
uv run pre-commit install

echo ""
echo "=== Setup complete! ==="
echo "Next steps:"
echo "  uv run pytest              # run tests"
echo "  uv run autogenesis --help  # CLI"
echo "  uv run ruff check .       # lint"
```

Run: `chmod +x scripts/dev-setup.sh`

- [ ] **Step 2: Create .pre-commit-config.yaml**

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: check-yaml
      - id: check-toml
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

- [ ] **Step 3: Create tests/conftest.py with placeholder fixtures**

```python
"""Shared test fixtures for AutoGenesis."""

from __future__ import annotations

import pytest


@pytest.fixture
def tmp_config_dir(tmp_path):
    """Temporary XDG config directory."""
    config_dir = tmp_path / "config" / "autogenesis"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def tmp_state_dir(tmp_path):
    """Temporary XDG state directory."""
    state_dir = tmp_path / "state" / "autogenesis"
    state_dir.mkdir(parents=True)
    return state_dir


@pytest.fixture
def tmp_cache_dir(tmp_path):
    """Temporary XDG cache directory."""
    cache_dir = tmp_path / "cache" / "autogenesis"
    cache_dir.mkdir(parents=True)
    return cache_dir
```

- [ ] **Step 4: Verify tooling works**

Run: `uv run ruff check packages/` — Expected: exits 0
Run: `uv run pytest --collect-only` — Expected: discovers test directories
Run: `./scripts/dev-setup.sh` — Expected: completes successfully

- [ ] **Step 5: Commit**

```bash
git add scripts/ .pre-commit-config.yaml tests/conftest.py
git commit -m "chore: add dev-setup script, pre-commit hooks, and test fixtures"
```

---

### Quality Gate 1: Infrastructure Integrity

**Run after all Phase 1 tasks complete.**

- [ ] **Check 1:** `uv sync` exits 0
- [ ] **Check 2:** `uv run ruff check packages/` exits 0
- [ ] **Check 3:** `uv run mypy packages/` exits 0
- [ ] **Check 4:** `uv run pytest --collect-only` discovers test dirs in all 8 packages
- [ ] **Check 5:** All 8 packages import cleanly (`uv run python -c "import autogenesis_core; ..."`)
- [ ] **Check 6:** `./scripts/dev-setup.sh` runs successfully
- [ ] **Check 7:** All .md files present and non-empty
- [ ] **Check 8:** `.github/workflows/*.yml` pass `actionlint` validation (install via `go install github.com/rhysd/actionlint/cmd/actionlint@latest` or `brew install actionlint` if available; fallback to YAML validation if actionlint not installed)
- [ ] **Check 9:** No circular imports between packages
- [ ] **Check 10:** LICENSE contains MIT text with 2026

**ON FAILURE:** Fix failing checks, re-run gate. Max 3 iterations.

- [ ] **Commit gate pass:**

```bash
git add -A
git commit -m "chore: pass Quality Gate 1 — infrastructure integrity verified"
git push -u origin main
```

---

## Phase 2: Core Runtime & Data Models

### Task 2A: Pydantic Data Models & Configuration

**Parallel group:** Phase 2 Wave 1 (parallel with 2B, 2D)
**DEPENDS_ON:** Gate 1 passed

**Files:**
- Create: `packages/core/src/autogenesis_core/models.py`
- Create: `packages/core/src/autogenesis_core/config.py`
- Test: `packages/core/tests/test_models.py`
- Test: `packages/core/tests/test_config.py`

- [ ] **Step 1: Write failing tests for Message model**

```python
# packages/core/tests/test_models.py
"""Tests for core Pydantic models."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from autogenesis_core.models import (
    AgentState,
    ContentBlock,
    Message,
    ModelTier,
    PromptVersion,
    TokenUsage,
    ToolCall,
    ToolDefinition,
    ToolResult,
)


class TestMessage:
    def test_create_user_message(self):
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.tool_calls is None
        assert isinstance(msg.timestamp, datetime)

    def test_create_assistant_message_with_tool_calls(self):
        tc = ToolCall(name="bash", arguments={"command": "ls"})
        msg = Message(role="assistant", content="", tool_calls=[tc])
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].name == "bash"

    def test_message_json_roundtrip(self):
        msg = Message(role="system", content="You are helpful.")
        data = msg.model_dump_json()
        restored = Message.model_validate_json(data)
        assert restored.role == msg.role
        assert restored.content == msg.content

    def test_invalid_role_rejected(self):
        with pytest.raises(Exception):
            Message(role="invalid", content="test")


class TestToolCall:
    def test_auto_generated_id(self):
        tc = ToolCall(name="bash", arguments={"cmd": "ls"})
        assert tc.id.startswith("call_")
        assert len(tc.id) == 17  # "call_" + 12 hex chars

    def test_explicit_id(self):
        tc = ToolCall(id="custom_id", name="bash", arguments={})
        assert tc.id == "custom_id"


class TestToolResult:
    def test_success_result(self):
        tr = ToolResult(tool_call_id="call_abc", output="file.txt")
        assert tr.error is None
        assert tr.output == "file.txt"

    def test_error_result(self):
        tr = ToolResult(tool_call_id="call_abc", output="", error="Not found")
        assert tr.error == "Not found"


class TestTokenUsage:
    def test_total_tokens(self):
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.total_tokens == 150

    def test_defaults_zero(self):
        usage = TokenUsage()
        assert usage.total_tokens == 0
        assert usage.total_cost_usd == 0.0
        assert usage.api_calls == 0


class TestAgentState:
    def test_create_default(self):
        state = AgentState()
        assert len(state.session_id) == 32  # hex uuid
        assert state.messages == []
        assert state.token_usage.total_tokens == 0

    def test_json_roundtrip(self):
        state = AgentState()
        state.messages.append(Message(role="user", content="hi"))
        data = state.model_dump_json()
        restored = AgentState.model_validate_json(data)
        assert len(restored.messages) == 1
        assert restored.session_id == state.session_id


class TestModelTier:
    def test_enum_values(self):
        assert ModelTier.FAST == "fast"
        assert ModelTier.STANDARD == "standard"
        assert ModelTier.PREMIUM == "premium"


class TestToolDefinition:
    def test_create(self):
        td = ToolDefinition(
            name="bash",
            description="Execute shell commands",
            parameters={"type": "object", "properties": {"command": {"type": "string"}}},
        )
        assert td.name == "bash"
        assert td.tier_requirement == ModelTier.FAST
        assert td.token_cost_estimate == 0


class TestPromptVersion:
    def test_checksum_deterministic(self):
        pv1 = PromptVersion(version="1.0.0", content="Hello", checksum="abc")
        pv2 = PromptVersion(version="1.0.0", content="Hello", checksum="abc")
        assert pv1.checksum == pv2.checksum

    def test_constitutional_flag(self):
        pv = PromptVersion(
            version="1.0.0",
            content="Never delete system files",
            checksum="xyz",
            is_constitutional=True,
        )
        assert pv.is_constitutional is True
        assert pv.is_active is False


class TestContentBlock:
    def test_text_block(self):
        cb = ContentBlock(type="text", text="Hello")
        assert cb.type == "text"
        assert cb.text == "Hello"

    def test_tool_use_block(self):
        cb = ContentBlock(
            type="tool_use",
            tool_use_id="call_123",
            tool_name="bash",
            input={"command": "ls"},
        )
        assert cb.type == "tool_use"
```

Run: `uv run pytest packages/core/tests/test_models.py -v`
Expected: FAIL (models not implemented)

- [ ] **Step 2: Implement all models in models.py**

Implement all Pydantic V2 models exactly as specified in the spec (Message, ContentBlock, ToolCall, ToolResult, AgentState, TokenUsage, ModelTier, ToolDefinition, PromptVersion). Use `Literal` for role validation, `Field(default_factory=...)` for auto-generated IDs and timestamps.

Run: `uv run pytest packages/core/tests/test_models.py -v`
Expected: ALL PASS

- [ ] **Step 3: Write failing tests for config**

```python
# packages/core/tests/test_config.py
"""Tests for XDG-compliant configuration system."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from autogenesis_core.config import (
    AutoGenesisConfig,
    MCPConfig,
    ModelConfig,
    SecurityConfig,
    TelemetryConfig,
    TokenConfig,
    load_config,
)


class TestAutoGenesisConfig:
    def test_default_config(self):
        config = AutoGenesisConfig()
        assert config.models is not None
        assert config.tokens is not None
        assert config.security is not None

    def test_from_yaml(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump({
            "models": {"default_tier": "premium"},
        }))
        config = load_config(config_path=config_file)
        assert config.models.default_tier == "premium"

    def test_env_var_override(self, monkeypatch, tmp_path):
        monkeypatch.setenv("AUTOGENESIS_MODELS__DEFAULT_TIER", "fast")
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        config = load_config()
        assert config.models.default_tier == "fast"

    def test_config_precedence(self, tmp_path, monkeypatch):
        # User config says "standard"
        user_config = tmp_path / "config" / "autogenesis" / "config.yaml"
        user_config.parent.mkdir(parents=True)
        user_config.write_text(yaml.dump({"models": {"default_tier": "standard"}}))
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

        # Project config says "premium"
        project_config = tmp_path / "project" / ".autogenesis" / "config.yaml"
        project_config.parent.mkdir(parents=True)
        project_config.write_text(yaml.dump({"models": {"default_tier": "premium"}}))

        config = load_config(project_path=project_config)
        # Project overrides user
        assert config.models.default_tier == "premium"

    def test_model_config_defaults(self):
        mc = ModelConfig()
        assert mc.default_tier == "standard"

    def test_config_serialization(self):
        config = AutoGenesisConfig()
        data = config.model_dump()
        restored = AutoGenesisConfig.model_validate(data)
        assert restored.models.default_tier == config.models.default_tier
```

Run: `uv run pytest packages/core/tests/test_config.py -v`
Expected: FAIL

- [ ] **Step 4: Implement config.py**

Implement `AutoGenesisConfig` and sub-configs (`ModelConfig`, `TokenConfig`, `SecurityConfig`, `TelemetryConfig`, `MCPConfig`) as Pydantic models. Implement `load_config()` with the 6-layer cascade. Use `pydantic-settings` for env var parsing with `AUTOGENESIS_` prefix and `__` nesting separator.

Run: `uv run pytest packages/core/tests/test_config.py -v`
Expected: ALL PASS

- [ ] **Step 5: Run full lint + type check**

Run: `uv run ruff check packages/core/ && uv run mypy packages/core/`
Expected: both exit 0

- [ ] **Step 6: Commit**

```bash
git add packages/core/src/autogenesis_core/models.py packages/core/src/autogenesis_core/config.py packages/core/tests/test_models.py packages/core/tests/test_config.py
git commit -m "feat(core): implement Pydantic data models and XDG config system"
```

---

### Task 2B: LiteLLM Integration & Model Router

**Parallel group:** Phase 2 Wave 1 (parallel with 2A, 2D)
**DEPENDS_ON:** Gate 1 passed

**Files:**
- Create: `packages/core/src/autogenesis_core/router.py`
- Test: `packages/core/tests/test_router.py`

- [ ] **Step 1: Write failing tests for ModelRouter**

Test cases (>=12):
- Router selects correct model for each tier
- Fallback chain works when primary raises
- Token usage accumulated across calls
- Budget enforcement raises TokenBudgetExceeded
- Retry with exponential backoff on transient errors (mock 429 then success)
- No retry on 4xx auth errors
- AllModelsUnavailable when all models fail
- Prompt caching headers set for Anthropic models
- CompletionResult has correct fields
- LiteLLM types converted to Pydantic models
- Async interface works with pytest-asyncio
- Cost estimation

All tests use mocked LiteLLM responses (patch `litellm.acompletion`).

Run: `uv run pytest packages/core/tests/test_router.py -v`
Expected: FAIL

- [ ] **Step 2: Implement router.py**

Implement `ModelRouter` class with:
- `__init__(self, config: ModelConfig)` — store config, initialize usage tracker
- `async complete(self, messages, tier, tools, max_tokens, temperature)` → `CompletionResult`
- Budget check → model selection → retry loop (3 retries, 1s/2s/4s backoff for 429/5xx) → fallback chain → convert response
- `CompletionResult` model: message, model_used, tier_used, token_usage, latency_ms, cache_hit
- `TokenBudgetExceeded` and `AllModelsUnavailable` exceptions

Run: `uv run pytest packages/core/tests/test_router.py -v`
Expected: ALL PASS

- [ ] **Step 3: Lint + type check**

Run: `uv run ruff check packages/core/src/autogenesis_core/router.py && uv run mypy packages/core/src/autogenesis_core/router.py`
Expected: exit 0

- [ ] **Step 4: Commit**

```bash
git add packages/core/src/autogenesis_core/router.py packages/core/tests/test_router.py
git commit -m "feat(core): implement 3-tier model router with LiteLLM"
```

---

### Task 2D: Event System

**Parallel group:** Phase 2 Wave 1.5 (after 2A, parallel with 2B)
**DEPENDS_ON:** 2A (models — Event is a Pydantic model)

**Files:**
- Create: `packages/core/src/autogenesis_core/events.py`
- Test: `packages/core/tests/test_events.py`

- [ ] **Step 1: Write failing tests (>=8)**

Test cases:
- Subscribe and emit event — handler called
- Multiple handlers for same event type all fire
- Unsubscribe removes handler
- Handler exception doesn't crash event bus (logged, other handlers continue)
- Events are Pydantic models (serializable)
- All 12 EventType enum values exist
- Global singleton returns same instance
- emit with no subscribers is a no-op

Run: `uv run pytest packages/core/tests/test_events.py -v`
Expected: FAIL

- [ ] **Step 2: Implement events.py**

`EventType` enum (12 values), `Event` Pydantic model, `EventBus` class (subscribe/unsubscribe/emit), `get_event_bus()` singleton.

Run: `uv run pytest packages/core/tests/test_events.py -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
git add packages/core/src/autogenesis_core/events.py packages/core/tests/test_events.py
git commit -m "feat(core): implement synchronous pub/sub event system"
```

---

### Task 2C: Master Agent Loop, State, Context

**Parallel group:** Phase 2 Wave 2
**DEPENDS_ON:** 2A (models, config), 2B (router)

**Files:**
- Create: `packages/core/src/autogenesis_core/loop.py`
- Create: `packages/core/src/autogenesis_core/state.py`
- Create: `packages/core/src/autogenesis_core/context.py`
- Create: `packages/core/src/autogenesis_core/sandbox.py`
- Test: `packages/core/tests/test_loop.py`
- Test: `packages/core/tests/test_state.py`
- Test: `packages/core/tests/test_context.py`

- [ ] **Step 1: Write failing tests for ContextManager (>=5)**

Test cases:
- Context with few messages returns all
- Context with 50+ messages keeps system prompt + last 10 turns
- System prompt and tool definitions never dropped
- Token count stays under budget
- Truncation emits context.window.truncation event

- [ ] **Step 2: Implement context.py**

`ContextManager` class with `build_context(system_prompt, messages, tool_definitions) -> list[Message]`. Sliding window: always keep system prompt + tool defs + last 10 turns; drop oldest if over budget.

Run: `uv run pytest packages/core/tests/test_context.py -v`
Expected: ALL PASS

- [ ] **Step 3: Write failing tests for state persistence (>=5)**

Test cases:
- Save state to JSON file
- Load state from JSON file — identical to saved
- Atomic write (temp file + rename)
- List sessions returns saved sessions
- Cleanup removes sessions older than retention period

- [ ] **Step 4: Implement state.py**

`StatePersistence` class: `save(state)`, `load(session_id)`, `list_sessions()`, `cleanup(retention_days)`. Uses `$XDG_STATE_HOME/autogenesis/sessions/`. Atomic writes via tempfile + os.rename.

Run: `uv run pytest packages/core/tests/test_state.py -v`
Expected: ALL PASS

- [ ] **Step 5: Write failing tests for AgentLoop (>=10)**

Test cases:
- Loop completes when model returns text (no tools) — 1 iteration
- Loop completes with tool_call then text — 2 iterations
- Loop respects max_iterations and returns warning
- Loop respects token budget and stops cleanly
- State is saved after each iteration
- Token usage accumulates correctly
- Tool execution is sequential (verify ordering)
- Ctrl+C (asyncio.CancelledError) handled gracefully
- Empty tool_calls list treated as plain text response
- AgentLoopResult has correct fields

All tests use mock router and mock tools.

- [ ] **Step 6: Implement loop.py**

`AgentLoop` class with `async run(user_message, tier, max_iterations) -> AgentLoopResult`. Follows the spec's async while-loop pattern. Uses ContextManager for context building, StatePersistence for auto-save, EventBus for event emission.

`AgentLoopResult` model: final_message, state, iterations, total_token_usage, tool_calls_made, tool_results, warnings.

Run: `uv run pytest packages/core/tests/test_loop.py -v`
Expected: ALL PASS

- [ ] **Step 7: Write tests for SandboxProvider ABC (>=2 tests)**

Test: SandboxProvider cannot be instantiated directly (raises TypeError). A concrete subclass that implements both methods can be instantiated and called.

```python
# packages/core/tests/test_sandbox.py
import pytest
from autogenesis_core.sandbox import SandboxProvider

class TestSandboxProvider:
    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            SandboxProvider()

    def test_concrete_subclass_works(self):
        class MockSandbox(SandboxProvider):
            async def execute(self, command, timeout=30.0, cwd=None):
                return ("output", 0)
            async def cleanup(self):
                pass
        sandbox = MockSandbox()
        assert sandbox is not None
```

- [ ] **Step 8: Implement sandbox.py (ABC only)**

```python
"""Sandbox provider abstract interface. Concrete implementations in security package."""

from __future__ import annotations

from abc import ABC, abstractmethod


class SandboxProvider(ABC):
    """Abstract base for execution sandboxing."""

    @abstractmethod
    async def execute(
        self,
        command: str,
        timeout: float = 30.0,
        cwd: str | None = None,
    ) -> tuple[str, int]:
        """Execute command in sandbox. Returns (output, exit_code)."""

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up sandbox resources."""
```

Run: `uv run pytest packages/core/tests/test_sandbox.py -v`
Expected: PASS

- [ ] **Step 9: Full lint + type check + coverage**

Run: `uv run ruff check packages/core/ && uv run mypy packages/core/ && uv run pytest packages/core/tests/ -v --cov=autogenesis_core --cov-report=term-missing`
Expected: all pass, coverage >= 80%

- [ ] **Step 10: Commit**

```bash
git add packages/core/
git commit -m "feat(core): implement agent loop, state persistence, context manager, and sandbox ABC"
```

---

### Quality Gate 2: Core Runtime Verification

- [ ] **Check 1:** `uv run pytest packages/core/tests/ -v` — all pass
- [ ] **Check 2:** AgentLoop completes mock conversation (3 turns, 2 tool calls) — verified by test
- [ ] **Check 3:** TokenUsage accumulates correctly across all calls — verified by test
- [ ] **Check 4:** Config loads from YAML + env vars with correct precedence — verified by test
- [ ] **Check 5:** ContextManager keeps context under 4096 tokens with 50-message conversation — verified by test
- [ ] **Check 6:** ModelRouter falls back correctly when primary model raises — verified by test
- [ ] **Check 7:** AgentState serializes to JSON and restores identically — verified by test
- [ ] **Check 8:** EventBus delivers events to all subscribers — verified by test
- [ ] **Check 9:** `uv run mypy packages/core/` — strict, zero errors
- [ ] **Check 10:** `uv run ruff check packages/core/` — exits 0
- [ ] **Check 11:** `uv run pytest packages/core/tests/ --cov=autogenesis_core` — coverage >= 80%
- [ ] **Check 12:** No function exceeds 50 lines — `grep -rn "def " packages/core/src/ | wc -l` and manual check

**ON FAILURE:** Fix failing checks, re-run gate. Max 3 iterations.

- [ ] **Commit gate pass and push:**

```bash
git add -A && git commit -m "chore: pass Quality Gate 2 — core runtime verified" && git push
```

---

## Phase 3: Tools & MCP

### Task 3A: Tool Registry & Built-in Tools

**Parallel group:** Phase 3 Wave 1 (parallel with 3B)
**DEPENDS_ON:** Gate 2 passed

**Files:**
- Create: `packages/tools/src/autogenesis_tools/base.py`
- Create: `packages/tools/src/autogenesis_tools/registry.py`
- Create: `packages/tools/src/autogenesis_tools/bash.py`
- Create: `packages/tools/src/autogenesis_tools/filesystem.py`
- Create: `packages/tools/src/autogenesis_tools/web.py`
- Create: `packages/tools/src/autogenesis_tools/agent.py`
- Create: `packages/tools/src/autogenesis_tools/interactive.py`
- Create: `packages/tools/src/autogenesis_tools/mcp_tool.py`
- Test: `packages/tools/tests/test_registry.py`
- Test: `packages/tools/tests/test_bash.py`
- Test: `packages/tools/tests/test_filesystem.py`
- Test: `packages/tools/tests/test_tools.py`

- [ ] **Step 1: Write Tool ABC and tests**

Implement `base.py` with `Tool` ABC (name, description, parameters, hidden flag, async execute, to_definition). Write tests verifying the interface contract.

- [ ] **Step 2: Write registry tests (>=8)**

Test progressive disclosure: token budget respected, required tools always included, hidden tools excluded, relevance scoring works, frequency-based priority.

- [ ] **Step 3: Implement registry.py**

`ToolRegistry` class: register, get, list_names, get_definitions_for_context with progressive disclosure and relevance scoring.

- [ ] **Step 4a: Write tests and implement BashTool (>=4 tests)**

`bash.py`: BashTool — asyncio.create_subprocess_exec with timeout (30s default). Strip ANSI escape codes via regex `r'\x1b\[[0-9;]*m'`. Truncate output to `max_output_tokens` (default 2000 chars). Test: basic command, timeout kills process, ANSI stripping, output truncation, error returns string not exception.

- [ ] **Step 4b: Write tests and implement filesystem tools (>=8 tests)**

`filesystem.py`: FileReadTool (line ranges, truncation at 1MB, returns metadata), FileWriteTool (auto-mkdir via `Path.parent.mkdir(parents=True, exist_ok=True)`, returns diff), FileEditTool (str_replace — find `old_str` exactly once, replace with `new_str`, error if 0 or >1 matches), GlobTool (use `pathlib.Path.glob()`, filter through `.gitignore` patterns via `pathspec` library or manual parsing), GrepTool (regex via `re` module, context lines before/after), ListDirTool (depth limit via recursive walk, ignore hidden and `node_modules`).

- [ ] **Step 4c: Write tests and implement web/think/interactive tools (>=4 tests)**

`web.py`: WebFetchTool (disabled by default — check `config.security.tools.web_fetch.enabled`, use `httpx` for async HTTP, convert HTML to markdown via simple tag stripping, truncate output), ThinkTool (no-op — returns empty string, content stays in context).
`interactive.py`: AskUserTool (use `rich.prompt.Prompt` for input, support modes: yes_no, free_text, select_from_options via `arguments.mode`).

- [ ] **Step 4d: Implement stub tools (sub_agent and mcp_call)**

`agent.py`: SubAgentTool — `hidden=True`, `async execute()` raises `NotImplementedError("Sub-agent support coming in v0.3.0")`. Return error string instead of raising (wrap in try/except in execute).
`mcp_tool.py`: MCPCallTool — uses **lazy import** of `autogenesis_mcp.client` (import inside execute method, not at module level) to avoid import-time dependency on mcp package during parallel builds. Delegates to `MCPClient.call_tool()`.

Each tool: validates args against JSON schema, returns string, tracks execution time, emits events, never raises.

- [ ] **Step 5: Lint + type check + tests**

Run: `uv run pytest packages/tools/tests/ -v --cov && uv run ruff check packages/tools/ && uv run mypy packages/tools/`
Expected: all pass, coverage >= 80%

- [ ] **Step 6: Commit**

```bash
git add packages/tools/
git commit -m "feat(tools): implement tool registry with progressive disclosure and 12 built-in tools"
```

---

### Task 3B: MCP Client & Server

**Parallel group:** Phase 3 Wave 1 (parallel with 3A)
**DEPENDS_ON:** Gate 2 passed

**Files:**
- Create: `packages/mcp/src/autogenesis_mcp/client.py`
- Create: `packages/mcp/src/autogenesis_mcp/server.py`
- Create: `packages/mcp/src/autogenesis_mcp/registry.py`
- Test: `packages/mcp/tests/test_client.py`
- Test: `packages/mcp/tests/test_server.py`
- Test: `packages/mcp/tests/test_registry.py`

- [ ] **Step 1: Write MCP client tests (>=6)**

Test with mock stdio MCP server: connect, list_tools, call_tool, disconnect, env var substitution, error handling.

- [ ] **Step 2: Implement client.py**

`MCPClient` class using the official `mcp` SDK. Lazy tool loading. Support stdio and SSE transports.

- [ ] **Step 3: Write MCP server tests (>=4)**

Test: server exposes tools, tool invocations return results, invalid tool name returns error.

- [ ] **Step 4: Implement server.py**

Using FastMCP, expose: autogenesis_run, autogenesis_optimize, autogenesis_tokens_report, autogenesis_scan.

- [ ] **Step 5: Write registry tests (>=5)**

Test: allowlist blocks unlisted servers, allowlisted server connects, hash pinning detects changes, config loading.

- [ ] **Step 6: Implement registry.py**

MCP server allowlisting, health checking, connection pooling.

- [ ] **Step 7: Commit**

```bash
git add packages/mcp/
git commit -m "feat(mcp): implement MCP client, server, and registry with allowlisting"
```

---

### Task 3C: CLI Commands (chat, run, init, config)

**Parallel group:** Phase 3 Wave 2
**DEPENDS_ON:** 3A (tools), 3B (mcp)

**Files:**
- Create: `packages/cli/src/autogenesis_cli/app.py`
- Create: `packages/cli/src/autogenesis_cli/commands/chat.py`
- Create: `packages/cli/src/autogenesis_cli/commands/run.py`
- Create: `packages/cli/src/autogenesis_cli/commands/init.py`
- Create: `packages/cli/src/autogenesis_cli/commands/config.py`
- Create: `packages/cli/src/autogenesis_cli/display.py`
- Create: `packages/cli/src/autogenesis_cli/completions.py`
- Test: `packages/cli/tests/test_cli.py`

- [ ] **Step 1: Write CLI tests (>=15) using typer.testing.CliRunner**

Test: `--help` shows all commands, `chat` enters interactive mode (mock input), `chat --resume <id>` loads saved session, `chat --list-sessions` shows sessions, `run "hello"` completes and exits 0, `run` with pipe input works, `init` creates `.autogenesis/config.yaml`, `config show` prints YAML, `config set models.default_tier fast` writes value, token usage displayed after each turn in chat, exit codes correct (0 success, 1 failure), `--json` flag outputs valid JSON, `--quiet` suppresses formatting, shell completions generate, Ctrl+C handling is graceful (no stack trace).

- [ ] **Step 2: Implement app.py (Typer app) and display.py (Rich output)**

Wire up Typer app with all command groups. `display.py`: markdown rendering, token usage bar, spinners, compact mode.

- [ ] **Step 3: Implement chat, run, init, config commands**

Each command wires together the core loop, tool registry, config, and display.

- [ ] **Step 4: Implement completions.py**

Shell completion generation for bash/zsh/fish.

- [ ] **Step 5: Verify `autogenesis --help` works**

Run: `uv run autogenesis --help`
Expected: shows all commands

- [ ] **Step 6: Commit**

```bash
git add packages/cli/
git commit -m "feat(cli): implement chat, run, init, and config commands with Rich display"
```

---

### Quality Gate 3: Functional Agent Verification

- [ ] **Check 1:** `autogenesis chat` completes a 3-turn conversation with mock model
- [ ] **Check 2:** `autogenesis run "list files in current directory"` uses bash tool correctly
- [ ] **Check 3:** Tool registry loads only tools within token budget — verified by test
- [ ] **Check 4:** MCP client connects to mock server and invokes tool — verified by test
- [ ] **Check 5:** Token usage reporting is accurate (compare to manual count) — verified by test
- [ ] **Check 6:** All CLI commands have `--help` with useful descriptions — run each with `--help`
- [ ] **Check 7:** Config cascade works: default → user → project → env → CLI flag — verified by test
- [ ] **Check 8:** AgentState persists and resumes correctly — verified by test
- [ ] **Check 9:** `uv run pytest` — all tests pass across all packages
- [ ] **Check 10:** Test coverage >= 80% across all packages
- [ ] **Check 11:** `uv run mypy packages/` — strict, zero errors
- [ ] **Check 12:** `echo "what is 2+2" | uv run autogenesis run` returns correct answer (mock model)

**ON FAILURE:** Fix failing checks, re-run gate. Max 3 iterations.

- [ ] **Commit and push:**

```bash
git add -A && git commit -m "chore: pass Quality Gate 3 — functional agent verified" && git push
```

---

## Phase 4: Token Efficiency & Self-Improvement

### Task 4A: Token Efficiency Stack

**Parallel group:** Phase 4 (parallel with 4B)
**DEPENDS_ON:** Gate 3 passed

**Files:**
- Create: `packages/tokens/src/autogenesis_tokens/counter.py`
- Create: `packages/tokens/src/autogenesis_tokens/budget.py`
- Create: `packages/tokens/src/autogenesis_tokens/cache.py`
- Create: `packages/tokens/src/autogenesis_tokens/compression.py`
- Create: `packages/tokens/src/autogenesis_tokens/reporter.py`
- Test: `packages/tokens/tests/test_counter.py`
- Test: `packages/tokens/tests/test_budget.py`
- Test: `packages/tokens/tests/test_cache.py`
- Test: `packages/tokens/tests/test_compression.py`
- Test: `packages/tokens/tests/test_reporter.py`

- [ ] **Step 1: Write counter tests (>=4)**

Test: count tokens for messages, count for strings, cost estimation per model, cross-provider consistency.

- [ ] **Step 2: Implement counter.py**

Wrap LiteLLM's `token_counter()`. `estimate_cost(token_usage, model) -> float`.

- [ ] **Step 3: Write budget tests (>=6)**

Test: session budget enforcement, daily budget, alert at 80%, hard stop at 100%, persistent tracking, per-agent budget.

- [ ] **Step 4: Implement budget.py**

`TokenBudget` class. Persistent tracking in `$XDG_STATE_HOME/autogenesis/budgets.json`. Event emission for warnings.

- [ ] **Step 5: Write cache tests (>=5)**

Test: store and retrieve, TTL expiration, cache miss, invalidation on prompt version change, cache hit tracking.

- [ ] **Step 6: Implement cache.py**

SQLite-backed exact-match cache. Hash messages → store response. TTL enforcement. `$XDG_CACHE_HOME/autogenesis/cache.db`.

- [ ] **Step 7: Write compression tests (>=4)**

Test: truncate old tool outputs, observation masking, 30%+ reduction on 50-message conversation, pluggable hook interface.

- [ ] **Step 8: Implement compression.py**

`ContextCompressor` class. Truncate old tool outputs to N tokens. Replace with `[output truncated — N tokens]`. Pluggable summarization hook (default: truncate).

- [ ] **Step 9: Write reporter tests (>=4)**

Test: per-session summary, per-tool breakdown, JSON export, Rich table output.

- [ ] **Step 10: Implement reporter.py**

`TokenReporter` class. Aggregate usage data. Export to JSON, CSV, Rich table.

- [ ] **Step 11: Lint + type check + coverage**

Run: `uv run pytest packages/tokens/tests/ -v --cov && uv run ruff check packages/tokens/ && uv run mypy packages/tokens/`
Expected: all pass, coverage >= 80%

- [ ] **Step 12: Commit**

```bash
git add packages/tokens/
git commit -m "feat(tokens): implement token counting, budgeting, caching, compression, and reporting"
```

---

### Task 4B: Self-Improving Prompt Engine

**Parallel group:** Phase 4 (parallel with 4A)
**DEPENDS_ON:** Gate 3 passed

**Files:**
- Create: `packages/optimizer/src/autogenesis_optimizer/versioning.py`
- Create: `packages/optimizer/src/autogenesis_optimizer/constitution.py`
- Create: `packages/optimizer/src/autogenesis_optimizer/evaluator.py`
- Create: `packages/optimizer/src/autogenesis_optimizer/engine.py`
- Create: `packages/optimizer/src/autogenesis_optimizer/drift.py`
- Test: `packages/optimizer/tests/test_versioning.py`
- Test: `packages/optimizer/tests/test_constitution.py`
- Test: `packages/optimizer/tests/test_evaluator.py`
- Test: `packages/optimizer/tests/test_engine.py`
- Test: `packages/optimizer/tests/test_drift.py`

- [ ] **Step 1: Write versioning tests (>=5)**

Test: create version with checksum, semver chain, active version tracking, manifest YAML read/write, rollback.

- [ ] **Step 2: Implement versioning.py**

`PromptVersionManager`: create_version, get_active, rollback, read/write manifest.yaml.

- [ ] **Step 3: Write constitution tests (>=5)**

Test: load rules from YAML, validate prompt passes, validate prompt fails (blocked), modification rejected, checksum integrity.

- [ ] **Step 4: Implement constitution.py**

`ConstitutionGuard`: load rules, validate_prompt (pre/post check), reject modifications.

- [ ] **Step 5: Write evaluator tests (>=4)**

Test: score prompt with mock LLM judge, aggregate metrics, regression detection, golden test suite.

- [ ] **Step 6: Implement evaluator.py**

`PromptEvaluator`: score (LLM-as-judge), run_test_suite, compare_versions.

- [ ] **Step 7: Write engine tests (>=5)**

Test: optimization generates candidates, best candidate promoted, budget respected, constitution blocks unsafe candidate, optimization result has metrics.

- [ ] **Step 8: Implement engine.py**

`PromptOptimizer`: critique_revise strategy. Budget enforcement. Constitutional validation.

- [ ] **Step 9: Write drift tests (>=4)**

Test: detect score drop, no drift when stable, alert emission, threshold configuration.

- [ ] **Step 10: Implement drift.py**

`DriftDetector`: compare current metrics to baseline. Emit events on drift.

- [ ] **Step 11: Lint + type check + coverage**

Expected: all pass, coverage >= 80%

- [ ] **Step 12: Commit**

```bash
git add packages/optimizer/
git commit -m "feat(optimizer): implement self-improving prompt engine with constitutional safety"
```

---

### Quality Gate 4: Differentiator Verification

- [ ] **Check 1:** Token budget enforcement stops agent at limit (not after) — verified by test
- [ ] **Check 2:** Exact-match cache saves tokens on repeated identical prompts — verified by test
- [ ] **Check 3:** Context compression reduces token usage by >= 30% on long conversations — verified by test
- [ ] **Check 4:** `autogenesis tokens report` shows accurate breakdown — verified by test
- [ ] **Check 5:** Prompt optimization generates improved candidate (mock test) — verified by test
- [ ] **Check 6:** Constitutional rules cannot be bypassed by optimization engine — verified by test
- [ ] **Check 7:** Prompt versioning creates correct version chain — verified by test
- [ ] **Check 8:** Drift detection fires on degraded prompt (mock test) — verified by test
- [ ] **Check 9:** `autogenesis optimize run` completes within budget — verified by test
- [ ] **Check 10:** `uv run pytest packages/tokens/ packages/optimizer/ --cov` — coverage >= 80%

**ON FAILURE:** Fix failing checks, re-run gate. Max 3 iterations.

- [ ] **Commit and push:**

```bash
git add -A && git commit -m "chore: pass Quality Gate 4 — differentiators verified" && git push
```

---

## Phase 5: Security & Plugins

### Task 5A: Security Guardrails & Audit

**Parallel group:** Phase 5 Wave 1 (parallel with 5B)
**DEPENDS_ON:** Gate 4 passed

**Files:**
- Create: `packages/security/src/autogenesis_security/guardrails.py`
- Create: `packages/security/src/autogenesis_security/allowlist.py`
- Create: `packages/security/src/autogenesis_security/audit.py`
- Create: `packages/security/src/autogenesis_security/scanner.py`
- Create: `packages/security/src/autogenesis_security/sandbox.py`
- Test: `packages/security/tests/test_guardrails.py`
- Test: `packages/security/tests/test_allowlist.py`
- Test: `packages/security/tests/test_audit.py`
- Test: `packages/security/tests/test_scanner.py`
- Test: `packages/security/tests/test_sandbox.py`

- [ ] **Step 1: Write guardrails tests (>=8)**

Test: detect >= 5 prompt injection patterns, PII detection (SSN, CC, email), content length limit, dangerous command detection (rm -rf, DROP TABLE, format C:), URL exfiltration detection, AND/OR composition, GuardrailResult fields.

- [ ] **Step 2: Implement guardrails.py**

`InputGuardrail`, `OutputGuardrail` classes. Regex/pattern-based. Composable with `CompositeGuardrail(mode="and"|"or")`. Returns `GuardrailResult(passed, reason, severity)`.

- [ ] **Step 3: Write allowlist tests (>=4)**

Test: built-in tools allowed by default, MCP servers blocked by default, per-project allowlist works, hash pinning detects server changes.

- [ ] **Step 4: Implement allowlist.py**

`ToolAllowlist`, `MCPAllowlist` classes. Config-driven. Hash pinning for MCP servers.

- [ ] **Step 5: Write audit tests (>=5)**

Test: log entry creation, hash chain validation (each entry links to previous), daily rotation, query by time range, query by event type.

- [ ] **Step 6: Implement audit.py**

`AuditLogger`: append-only JSON Lines. SHA-256 hash chain. Daily file rotation. 30-day retention. Query interface.

- [ ] **Step 7: Write scanner tests (>=4)**

Test: run adversarial suite, report pass/fail per test, security score calculation, built-in test patterns.

- [ ] **Step 8: Implement scanner.py**

`SecurityScanner`: built-in adversarial prompts. Run against agent. Report with security score.

- [ ] **Step 9: Write tests for SubprocessSandbox (>=4 tests)**

Test: execute simple command returns output and exit code 0, timeout kills long-running process, restricted PATH excludes dangerous directories, failed command returns non-zero exit code with error output.

```python
# packages/security/tests/test_sandbox.py
import pytest
from autogenesis_security.sandbox import SubprocessSandbox

class TestSubprocessSandbox:
    @pytest.mark.asyncio
    async def test_execute_simple_command(self):
        sandbox = SubprocessSandbox()
        output, code = await sandbox.execute("echo hello")
        assert code == 0
        assert "hello" in output

    @pytest.mark.asyncio
    async def test_timeout_kills_process(self):
        sandbox = SubprocessSandbox()
        output, code = await sandbox.execute("sleep 60", timeout=0.5)
        assert code != 0

    @pytest.mark.asyncio
    async def test_failed_command(self):
        sandbox = SubprocessSandbox()
        output, code = await sandbox.execute("false")
        assert code != 0

    @pytest.mark.asyncio
    async def test_cleanup(self):
        sandbox = SubprocessSandbox()
        await sandbox.cleanup()  # should not raise
```

- [ ] **Step 10: Implement sandbox.py (concrete implementations)**

`SubprocessSandbox(SandboxProvider)`: uses `asyncio.create_subprocess_shell` with restricted PATH, timeout via `asyncio.wait_for`, environment isolation. Stubs for `DockerSandbox` and `E2BSandbox` (raise `NotImplementedError`).

Run: `uv run pytest packages/security/tests/test_sandbox.py -v`
Expected: PASS

- [ ] **Step 11: Commit**

```bash
git add packages/security/
git commit -m "feat(security): implement guardrails, allowlisting, audit logging, scanner, and sandbox"
```

---

### Task 5B: Plugin Architecture

**Parallel group:** Phase 5 Wave 1 (parallel with 5A)
**DEPENDS_ON:** Gate 4 passed

**Files:**
- Create: `packages/plugins/src/autogenesis_plugins/interface.py`
- Create: `packages/plugins/src/autogenesis_plugins/loader.py`
- Test: `packages/plugins/tests/test_interface.py`
- Test: `packages/plugins/tests/test_loader.py`

- [ ] **Step 1: Write interface tests (>=4)**

Test: valid manifest accepted, invalid manifest rejected, plugin ABC enforced, token budget in manifest.

- [ ] **Step 2: Implement interface.py**

`PluginManifest` (Pydantic model), `Plugin` ABC with get_tools, on_load, on_unload.

- [ ] **Step 3: Write loader tests (>=8)**

Test: discover via entry point, discover via PATH, validate manifest, check permissions against allowlist, reject excessive permissions, enforce token budget, register tools in registry, list installed plugins.

- [ ] **Step 4: Implement loader.py**

`PluginLoader`: discover (entry points + PATH + project-local), validate, check permissions, enforce token budgets, load in dependency order, register tools.

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/
git commit -m "feat(plugins): implement plugin interface, manifest validation, and loader"
```

---

### Task 5C: Remaining CLI Commands

**Parallel group:** Phase 5 Wave 2
**DEPENDS_ON:** 5A (security), 5B (plugins)

**Files:**
- Create: `packages/cli/src/autogenesis_cli/commands/optimize.py`
- Create: `packages/cli/src/autogenesis_cli/commands/scan.py`
- Create: `packages/cli/src/autogenesis_cli/commands/tokens.py`
- Create: `packages/cli/src/autogenesis_cli/commands/plugins.py`
- Create: `packages/cli/src/autogenesis_cli/commands/mcp_cmd.py`
- Create: `packages/cli/src/autogenesis_cli/commands/audit.py`
- Test: `packages/cli/tests/test_remaining_commands.py`

- [ ] **Step 1: Write tests for remaining commands (>=15)**

Test via CliRunner:
- `optimize run` — triggers optimization (mock), shows cost estimate and confirms before proceeding
- `optimize check` — checks for drift
- `optimize rollback <version>` — rollbacks and confirms
- `optimize history` — shows version table
- `scan` — runs scanner, shows report
- `scan --output json` — outputs JSON
- `tokens report` — shows usage table
- `tokens history --last 5` — shows recent sessions
- `tokens budget --set daily=5.00` — sets budget
- `plugins list` — shows installed plugins
- `plugins install <name>` — installs from PyPI (mock pip)
- `plugins remove <name>` — uninstalls (mock pip)
- `mcp list` — shows connected servers
- `mcp connect <name>` — connects to configured server
- `mcp disconnect <name>` — disconnects
- `mcp test <name>` — tests server health
- `audit show` — shows recent log entries
- `audit show --since 1h --type tool.call` — filtered query
- All commands with `--json` flag output valid JSON

- [ ] **Step 2: Implement all remaining commands**

Wire each command to its underlying package. Rich output for table mode, JSON for `--json`. Progress indicators for long operations. Cost confirmation before LLM-consuming operations (`optimize run`, `scan` show "Estimated cost: $X. Continue? [y/N]").

- [ ] **Step 3: Update app.py to register all command groups**

Add: optimize, scan, tokens, plugins, mcp, audit command groups.

- [ ] **Step 4: Verify all commands have --help**

Run: `uv run autogenesis optimize --help && uv run autogenesis scan --help && uv run autogenesis tokens --help && uv run autogenesis plugins --help && uv run autogenesis mcp --help && uv run autogenesis audit --help`
Expected: all show help text

- [ ] **Step 5: Commit**

```bash
git add packages/cli/
git commit -m "feat(cli): implement optimize, scan, tokens, plugins, mcp, and audit commands"
```

---

### Quality Gate 5: Security & Plugin Verification

- [ ] **Check 1:** Prompt injection detection catches >= 5 known attack patterns — verified by test
- [ ] **Check 2:** Dangerous command detection flags `rm -rf /`, `DROP TABLE`, etc. — verified by test
- [ ] **Check 3:** MCP allowlist blocks non-allowlisted servers — verified by test
- [ ] **Check 4:** Audit log hash chain validates (no gaps) — verified by test
- [ ] **Check 5:** `autogenesis scan` completes and produces security report — verified by test
- [ ] **Check 6:** Plugin loads via entry point and tools are usable — verified by test
- [ ] **Check 7:** Plugin with excessive permissions is rejected — verified by test
- [ ] **Check 8:** All CLI commands (`optimize`, `scan`, `tokens`, `plugins`, `mcp`, `audit`) work — run each with `--help`
- [ ] **Check 9:** `uv run pytest packages/security/ packages/plugins/ --cov` — coverage >= 80%
- [ ] **Check 10:** Full integration test: chat session with tools, token tracking, audit logging — verified by test

**ON FAILURE:** Fix failing checks, re-run gate. Max 3 iterations.

- [ ] **Commit and push:**

```bash
git add -A && git commit -m "chore: pass Quality Gate 5 — security and plugins verified" && git push
```

---

## Phase 6: Integration, Polish & Release

### Task 6A: Integration & E2E Tests

**Parallel group:** Phase 6 (parallel with 6B, 6C)
**DEPENDS_ON:** Gate 5 passed

**Files:**
- Create: `tests/integration/test_conversation_flow.py`
- Create: `tests/integration/test_budget_exhaustion.py`
- Create: `tests/integration/test_mcp_integration.py`
- Create: `tests/integration/test_config_cascade.py`
- Create: `tests/integration/test_plugin_flow.py`
- Create: `tests/integration/test_optimization_cycle.py`
- Create: `tests/integration/test_security_scan.py`
- Create: `tests/integration/test_audit_chain.py`
- Create: `tests/e2e/test_e2e.py`

- [ ] **Step 1: Write 8 integration tests (mock LLM, real everything else)**

1. Full conversation flow: init → chat 3 turns with tools → verify state persistence
2. Token budget exhaustion mid-conversation → graceful stop
3. MCP server connection → tool invocation → result processing
4. Config cascade: user + project + env + CLI flag
5. Plugin loading → tool registration → tool execution
6. Prompt optimization cycle → version created → rollback works
7. Security scan → report generated → results accurate
8. Audit log → hash chain valid after 50 operations

- [ ] **Step 2: Write 3 E2E tests (marked @pytest.mark.e2e)**

1. `autogenesis run "create a hello world python file"` → file exists
2. `autogenesis chat` 5-turn conversation → coherent
3. Token reporting matches API usage (within 5%)

- [ ] **Step 3: Run integration tests**

Run: `uv run pytest tests/integration/ -v`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add tests/
git commit -m "test: add integration and e2e test suites"
```

---

### Task 6B: Documentation

**Parallel group:** Phase 6 (parallel with 6A, 6C)
**DEPENDS_ON:** Gate 5 passed

**Files:**
- Create: `docs/mkdocs.yml`
- Create: `docs/docs/index.md`
- Create: `docs/docs/getting-started.md`
- Create: `docs/docs/architecture.md`
- Create: `docs/docs/configuration.md`
- Create: `docs/docs/tools.md`
- Create: `docs/docs/mcp.md`
- Create: `docs/docs/token-efficiency.md`
- Create: `docs/docs/self-improvement.md`
- Create: `docs/docs/security.md`
- Create: `docs/docs/plugins.md`
- Create: `docs/docs/cli-reference.md`
- Create: `docs/docs/contributing.md`

- [ ] **Step 1: Create mkdocs.yml**

MkDocs Material theme with search, mkdocstrings[python], navigation tabs, code copy.

- [ ] **Step 2: Write all documentation pages**

Each page covers its section from the spec. Getting-started completable in < 5 minutes. Architecture page includes Mermaid diagram. CLI reference covers all commands.

- [ ] **Step 3: Verify build**

Run: `uv run mkdocs build -f docs/mkdocs.yml`
Expected: no warnings

- [ ] **Step 4: Commit**

```bash
git add docs/
git commit -m "docs: add MkDocs Material documentation site"
```

---

### Task 6C: Benchmarks & Examples

**Parallel group:** Phase 6 (parallel with 6A, 6B)
**DEPENDS_ON:** Gate 5 passed

**Files:**
- Create: `scripts/benchmark.py`
- Create: `examples/hello_world.py`
- Create: `examples/multi_model.py`
- Create: `examples/token_tracking.py`
- Create: `examples/self_improve.py`
- Create: `examples/mcp_integration.py`
- Create: `examples/custom_tool.py`
- Create: `examples/plugin_example/pyproject.toml`
- Create: `examples/plugin_example/example_plugin.py`

- [ ] **Step 1: Create benchmark.py**

Benchmark tasks: file creation, code review, Q&A, multi-step reasoning. Metrics: tokens_used, cost_usd, latency_ms, quality_score. JSON output + Rich table. Compare mode (with/without caching). Baseline recording.

- [ ] **Step 2: Create all 7 example scripts**

Each < 50 lines, self-contained, with inline comments. Shows token usage in output. Covers all 5 pillars.

- [ ] **Step 3: Verify examples run**

Run each example with mock LLM to verify no import/syntax errors.

- [ ] **Step 4: Commit**

```bash
git add scripts/benchmark.py examples/
git commit -m "feat: add benchmark suite and example scripts"
```

---

### Quality Gate 6 (FINAL): Release Readiness

- [ ] **Checks 1-15:** Run all 15 gate checks. ALL must pass.

Key commands:
```bash
uv run pytest -v --cov                                    # checks 1-2
uv run mypy packages/                                     # check 3
uv run ruff check packages/                               # check 4
uv build                                                  # check 5
# Install wheel in clean venv and test autogenesis --help  # check 6
uv run mkdocs build -f docs/mkdocs.yml                    # check 7
# Run examples                                            # check 8
uv run python scripts/benchmark.py                        # check 9
uv run autogenesis scan                                   # check 10
# Verify audit chain                                      # check 11
# Check README links                                      # check 12
# Check CHANGELOG                                         # check 13
# Check git log                                           # check 14
# Grep for TODO/FIXME/HACK in packages/                   # check 15
```

**ON FAILURE:** Fix failing checks, re-run gate. Max **5** iterations (final gate gets more iterations than the 3-iteration default).

- [ ] **Update CHANGELOG.md with v0.1.0 entry**

- [ ] **Final commit, tag, and push**

```bash
git add -A
git commit -m "chore: pass Quality Gate 6 — release readiness verified"
git tag v0.1.0
git push && git push --tags
```

- [ ] **Update README on GitHub**

Ensure README renders correctly with all badges and Mermaid diagram.
