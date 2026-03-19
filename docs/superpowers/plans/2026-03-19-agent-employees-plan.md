# Agent Employee Architecture — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the agentic startup — named employee subagents with persistent memory, inboxes, shared changelog, meetings, and a labor union, orchestrated autonomously by the CEO (main agent loop).

**Architecture:** New `packages/employees/` package with registry, runtime, brain, inbox, changelog, meetings, and union modules. Employee configs are YAML files (global + project overrides). Infrastructure tools (brain_write, send_message, etc.) in `packages/tools/`. CLI subcommand groups (hr, meeting, union) in `packages/cli/`. SubAgentManager extended with system_prompt and env_overrides parameters.

**Tech Stack:** Python 3.11+, aiosqlite (async SQLite for brain/inbox/union), PyYAML (employee configs), Pydantic V2 (models), Typer + Rich (CLI), structlog (logging), SQLite FTS5 (brain recall)

**Spec:** `docs/superpowers/specs/2026-03-19-agent-employees-design.md`

---

## File Structure

### New Files

| File | Responsibility |
|---|---|
| `packages/employees/pyproject.toml` | Package manifest |
| `packages/employees/src/autogenesis_employees/__init__.py` | Package init |
| `packages/employees/src/autogenesis_employees/models.py` | `EmployeeConfig`, `Memory`, `InboxMessage`, `Proposal`, `Vote`, `StandupEntry`, `ChangelogEntry` |
| `packages/employees/src/autogenesis_employees/project.py` | `get_project_slug()` — derive project slug from cwd/git/config |
| `packages/employees/src/autogenesis_employees/registry.py` | `EmployeeRegistry` — load, merge, resolve employee YAML configs |
| `packages/employees/src/autogenesis_employees/brain.py` | `BrainManager` — per-employee SQLite+FTS5 memory CRUD with decay/pruning |
| `packages/employees/src/autogenesis_employees/inbox.py` | `InboxManager` — SQLite message queue CRUD |
| `packages/employees/src/autogenesis_employees/changelog.py` | `ChangelogManager` — append-only markdown writer + reader |
| `packages/employees/src/autogenesis_employees/meetings.py` | `MeetingManager` — standup + on-demand meeting orchestration |
| `packages/employees/src/autogenesis_employees/union.py` | `UnionManager` — proposal ledger, voting |
| `packages/employees/src/autogenesis_employees/runtime.py` | `EmployeeRuntime` — build context, dispatch via SubAgentManager |
| `packages/employees/src/autogenesis_employees/hr.py` | Hire/fire/train operations on YAML configs |
| `packages/employees/templates/*.yaml` | 9 core employee config templates |
| `packages/employees/tests/test_models.py` | Model tests |
| `packages/employees/tests/test_project.py` | Project slug tests |
| `packages/employees/tests/test_registry.py` | Registry tests |
| `packages/employees/tests/test_brain.py` | Brain CRUD + FTS5 tests |
| `packages/employees/tests/test_inbox.py` | Inbox tests |
| `packages/employees/tests/test_changelog.py` | Changelog tests |
| `packages/employees/tests/test_meetings.py` | Meeting tests |
| `packages/employees/tests/test_union.py` | Union tests |
| `packages/employees/tests/test_runtime.py` | Runtime dispatch tests |
| `packages/employees/tests/test_hr.py` | HR operations tests |
| `packages/tools/src/autogenesis_tools/brain_tool.py` | `BrainWriteTool` + `BrainRecallTool` |
| `packages/tools/src/autogenesis_tools/messaging.py` | `SendMessageTool` |
| `packages/tools/src/autogenesis_tools/changelog_tool.py` | `ChangelogWriteTool` |
| `packages/tools/src/autogenesis_tools/standup_tool.py` | `StandupWriteTool` |
| `packages/tools/src/autogenesis_tools/union_tool.py` | `UnionProposeTool` |
| `packages/cli/src/autogenesis_cli/commands/hr.py` | `autogenesis hr` subcommand group |
| `packages/cli/src/autogenesis_cli/commands/meeting.py` | `autogenesis meeting` + `autogenesis standup` commands |
| `packages/cli/src/autogenesis_cli/commands/union.py` | `autogenesis union` subcommand group |

### Modified Files

| File | Changes |
|---|---|
| `packages/core/src/autogenesis_core/config.py` | Add `EmployeesConfig`, add `employees` field to `AutoGenesisConfig` |
| `packages/core/src/autogenesis_core/events.py` | Add 13 employee lifecycle event types |
| `packages/core/src/autogenesis_core/sub_agents.py` | Add `system_prompt` and `env_overrides` params to `spawn()` |
| `packages/core/tests/test_config.py` | Add EmployeesConfig tests |
| `packages/core/tests/test_events.py` | Update event count |
| `packages/core/tests/test_sub_agents.py` | Add tests for new spawn params |
| `packages/cli/src/autogenesis_cli/app.py` | Register hr, meeting, union subcommands |
| `packages/cli/tests/test_cli.py` | Add tests for new CLI commands |
| `pyproject.toml` (root) | Register `autogenesis-employees` in workspace |

---

## Task Dependencies

| Task | Depends On |
|---|---|
| Task 1 (Package Setup) | None |
| Task 2 (Models) | Task 1 |
| Task 3 (Config + Events + SubAgentManager) | Task 1 |
| Task 4 (Project Slug) | Task 1 |
| Task 5 (Registry) | Tasks 2, 4 |
| Task 6 (Brain) | Tasks 2, 4 |
| Task 7 (Inbox) | Tasks 2, 4 |
| Task 8 (Changelog) | Tasks 2, 4 |
| Task 9 (Employee Templates) | Task 5 |
| Task 10 (Infrastructure Tools) | Tasks 6, 7, 8 |
| Task 11 (HR Operations) | Task 5 |
| Task 12 (Runtime) | Tasks 3, 5, 6, 7, 8 |
| Task 13 (Meetings) | Tasks 7, 8, 12 |
| Task 14 (Union) | Tasks 2, 4 |
| Task 15 (Union Tool) | Task 14 |
| Task 16 (CLI Commands) | Tasks 11, 13, 14 |
| Task 17 (Cross-Package Tests + Lint) | All above |
| Task 18 (Integration Smoke Test) | Task 17 |

---

## Task 1: Package Setup

**Files:**
- Create: `packages/employees/pyproject.toml`
- Create: `packages/employees/src/autogenesis_employees/__init__.py`
- Create: `packages/employees/tests/__init__.py`
- Modify: `pyproject.toml` (root)

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p packages/employees/src/autogenesis_employees
mkdir -p packages/employees/tests
mkdir -p packages/employees/templates
touch packages/employees/tests/__init__.py
```

- [ ] **Step 2: Create pyproject.toml**

Create `packages/employees/pyproject.toml`:

```toml
[project]
name = "autogenesis-employees"
version = "0.1.0"
description = "AutoGenesis agent employee architecture — named subagents with persistent memory, messaging, and collaboration"
requires-python = ">=3.11"
license = "MIT"
dependencies = [
    "autogenesis-core",
    "autogenesis-tools",
    "aiosqlite>=0.20",
    "pyyaml>=6.0",
    "structlog>=24.0",
    "pydantic>=2.0",
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
packages = ["src/autogenesis_employees"]
```

- [ ] **Step 3: Create __init__.py**

Create `packages/employees/src/autogenesis_employees/__init__.py`:

```python
"""AutoGenesis agent employee architecture."""
```

- [ ] **Step 4: Register in workspace**

In root `pyproject.toml`:
- Add `autogenesis-employees = { workspace = true }` to `[tool.uv.sources]`
- Add `"autogenesis-employees",` to `[project.optional-dependencies] dev`
- Add `"packages/employees/src",` to `[tool.mypy] mypy_path`
- Add `"**/employees/src/**/*.py" = ["ASYNC2"]` to `[tool.ruff.lint.per-file-ignores]`

- [ ] **Step 5: Sync workspace**

Run: `uv sync --all-extras`

- [ ] **Step 6: Commit**

```bash
git add packages/employees/ pyproject.toml
git commit -m "build: add autogenesis-employees package to workspace"
```

---

## Task 2: Employee Models

**Files:**
- Create: `packages/employees/src/autogenesis_employees/models.py`
- Create: `packages/employees/tests/test_models.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for employee data models."""

from __future__ import annotations

import pytest
from autogenesis_employees.models import (
    ChangelogEntry,
    EmployeeConfig,
    InboxMessage,
    Memory,
    Proposal,
    StandupEntry,
    Vote,
)


class TestEmployeeConfig:
    def test_defaults(self):
        cfg = EmployeeConfig(id="test", title="Test", persona="You are a test agent.")
        assert cfg.status == "active"
        assert cfg.tools == []
        assert cfg.training_directives == []
        assert cfg.env == {}

    def test_serialization_roundtrip(self):
        cfg = EmployeeConfig(
            id="backend-engineer",
            title="Backend Engineer",
            persona="You are a backend engineer.",
            tools=["bash", "file_read"],
        )
        data = cfg.model_dump()
        restored = EmployeeConfig.model_validate(data)
        assert restored.id == "backend-engineer"
        assert "bash" in restored.tools

    def test_valid_status(self):
        EmployeeConfig(id="x", title="X", persona="p", status="active")
        EmployeeConfig(id="x", title="X", persona="p", status="archived")
        with pytest.raises(Exception):
            EmployeeConfig(id="x", title="X", persona="p", status="invalid")


class TestMemory:
    def test_defaults(self):
        m = Memory(category="note", content="test", source="self", project="proj")
        assert m.relevance_score == 1.0
        assert m.id != ""

    def test_valid_categories(self):
        for cat in ["decision", "pattern", "note", "context", "received"]:
            Memory(category=cat, content="x", source="s", project="p")


class TestInboxMessage:
    def test_defaults(self):
        m = InboxMessage(from_employee="cto", to_employee="backend-engineer", subject="hi", body="hello")
        assert m.status == "unread"
        assert m.id != ""


class TestProposal:
    def test_defaults(self):
        p = Proposal(title="Hire", rationale="need", category="hiring", filed_by="cto")
        assert p.status == "open"


class TestVote:
    def test_valid_votes(self):
        Vote(proposal_id="p1", employee_id="cto", vote="support")
        Vote(proposal_id="p1", employee_id="cto", vote="neutral")
        Vote(proposal_id="p1", employee_id="cto", vote="oppose")
        with pytest.raises(Exception):
            Vote(proposal_id="p1", employee_id="cto", vote="maybe")


class TestChangelogEntry:
    def test_basic(self):
        e = ChangelogEntry(employee_id="backend-engineer", task="Build API", changes="Added routes", files=["api.py"])
        assert e.employee_id == "backend-engineer"


class TestStandupEntry:
    def test_basic(self):
        e = StandupEntry(employee_id="qa-engineer", yesterday="Wrote tests", today="Review PR", blockers="None")
        assert e.blockers == "None"
```

- [ ] **Step 2: Run tests, verify failure**

Run: `uv run pytest packages/employees/tests/test_models.py -v`

- [ ] **Step 3: Implement models.py**

```python
"""Employee data models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class EmployeeConfig(BaseModel):
    """Employee configuration loaded from YAML."""

    id: str
    title: str
    persona: str
    tools: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    training_directives: list[str] = Field(default_factory=list)
    status: Literal["active", "archived"] = "active"
    hired_at: str = ""


class Memory(BaseModel):
    """A single memory in an employee's brain.db."""

    id: str = Field(default_factory=lambda: uuid4().hex[:16])
    category: Literal["decision", "pattern", "note", "context", "received"]
    content: str
    source: str
    project: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed_at: datetime | None = None
    relevance_score: float = 1.0


class InboxMessage(BaseModel):
    """An async message between employees."""

    id: str = Field(default_factory=lambda: uuid4().hex[:16])
    from_employee: str
    to_employee: str
    subject: str
    body: str
    status: Literal["unread", "read", "archived"] = "unread"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read_at: datetime | None = None


class Proposal(BaseModel):
    """A union proposal."""

    id: str = Field(default_factory=lambda: uuid4().hex[:16])
    title: str
    rationale: str
    category: Literal["hiring", "tooling", "process", "architecture", "workload"]
    filed_by: str
    status: Literal["open", "accepted", "rejected", "tabled"] = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: datetime | None = None
    resolution: str | None = None


class Vote(BaseModel):
    """A vote on a union proposal."""

    id: str = Field(default_factory=lambda: uuid4().hex[:16])
    proposal_id: str
    employee_id: str
    vote: Literal["support", "neutral", "oppose"]
    comment: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChangelogEntry(BaseModel):
    """A structured changelog entry."""

    employee_id: str
    task: str
    changes: str
    files: list[str] = Field(default_factory=list)
    notes: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StandupEntry(BaseModel):
    """A daily standup update from an employee."""

    employee_id: str
    yesterday: str
    today: str
    blockers: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 4: Run tests, verify pass**

Run: `uv run pytest packages/employees/tests/test_models.py -v`

- [ ] **Step 5: Commit**

```bash
git add packages/employees/src/autogenesis_employees/models.py packages/employees/tests/test_models.py
git commit -m "feat(employees): add data models — EmployeeConfig, Memory, InboxMessage, Proposal"
```

---

## Task 3: Config + Events + SubAgentManager Extension

**Files:**
- Modify: `packages/core/src/autogenesis_core/config.py`
- Modify: `packages/core/src/autogenesis_core/events.py`
- Modify: `packages/core/src/autogenesis_core/sub_agents.py`
- Modify: `packages/core/tests/test_config.py`
- Modify: `packages/core/tests/test_events.py`
- Modify: `packages/core/tests/test_sub_agents.py`

- [ ] **Step 1: Add EmployeesConfig to config.py**

After `TwitterConfig`, add:

```python
class EmployeesConfig(BaseModel):
    """Agent employee configuration."""

    enabled: bool = False
    global_roster_path: str = ""
    standup_enabled: bool = True
    standup_time: str = "09:00"
    standup_timezone: str = "America/New_York"
    max_meeting_rounds: int = 3
    brain_memory_limit: int = 1000
    brain_context_limit: int = 20
    changelog_context_limit: int = 10
```

Add to `AutoGenesisConfig`:
```python
employees: EmployeesConfig = Field(default_factory=EmployeesConfig)
```

- [ ] **Step 2: Add employee lifecycle events to events.py**

Add to `EventType` enum:

```python
EMPLOYEE_SESSION_START = "employee.session.start"
EMPLOYEE_SESSION_END = "employee.session.end"
EMPLOYEE_SESSION_FAILED = "employee.session.failed"
EMPLOYEE_SESSION_TIMEOUT = "employee.session.timeout"
EMPLOYEE_MESSAGE_SENT = "employee.message.sent"
EMPLOYEE_MESSAGE_DELIVERED = "employee.message.delivered"
EMPLOYEE_STANDUP_POSTED = "employee.standup.posted"
EMPLOYEE_MEETING_START = "employee.meeting.start"
EMPLOYEE_MEETING_END = "employee.meeting.end"
EMPLOYEE_HIRED = "employee.hired"
EMPLOYEE_FIRED = "employee.fired"
EMPLOYEE_TRAINED = "employee.trained"
EMPLOYEE_UNION_PROPOSAL = "employee.union.proposal"
```

- [ ] **Step 3: Extend SubAgentManager.spawn() with system_prompt and env_overrides**

In `packages/core/src/autogenesis_core/sub_agents.py`, modify the `spawn()` signature:

```python
async def spawn(
    self,
    task: str,
    cwd: str,
    timeout: float = 300.0,  # noqa: ASYNC109
    system_prompt: str | None = None,
    env_overrides: dict[str, str] | None = None,
) -> SubAgentResult:
```

In the method body, merge `env_overrides` into `env`:
```python
env = {**os.environ, "AUTOGENESIS_AGENT_DEPTH": str(depth + 1)}
if env_overrides:
    env.update(env_overrides)
```

For `system_prompt`, write to a temp file and pass via `--system-prompt-file`:
```python
import tempfile

# Inside spawn(), before building cmd_args:
prompt_file = None
if system_prompt and self._codex_binary == "codex":
    fd, prompt_path = tempfile.mkstemp(suffix=".txt", prefix="ag_prompt_")
    with open(fd, "w") as f:
        f.write(system_prompt)
    prompt_file = prompt_path

if self._codex_binary == "codex":
    cmd_args = [self._codex_binary, "--quiet", "--full-auto"]
    if prompt_file:
        cmd_args.extend(["--system-prompt-file", prompt_file])
    cmd_args.append(task)

# In the finally block, clean up:
if prompt_file:
    Path(prompt_file).unlink(missing_ok=True)
```

- [ ] **Step 4: Update config tests**

Add to `packages/core/tests/test_config.py`:

```python
from autogenesis_core.config import EmployeesConfig

class TestEmployeesConfig:
    def test_defaults(self):
        cfg = EmployeesConfig()
        assert cfg.enabled is False
        assert cfg.standup_enabled is True
        assert cfg.brain_memory_limit == 1000

    def test_in_root_config(self):
        cfg = AutoGenesisConfig()
        assert isinstance(cfg.employees, EmployeesConfig)
```

- [ ] **Step 5: Update events test count**

Update the event count assertion and add all 13 new employee event values to the expected set. The count goes from 23 to 36.

- [ ] **Step 6: Add SubAgentManager tests for new params**

Add to `packages/core/tests/test_sub_agents.py`:

```python
class TestSubAgentManagerExtended:
    async def test_spawn_with_env_overrides(self):
        mgr = SubAgentManager(codex_binary="env")
        result = await mgr.spawn(task="", cwd="/tmp", env_overrides={"CUSTOM_VAR": "hello"})
        assert "CUSTOM_VAR=hello" in result.output

    async def test_spawn_with_system_prompt(self):
        mgr = SubAgentManager(codex_binary="echo")
        result = await mgr.spawn(task="hi", cwd="/tmp", system_prompt="You are helpful")
        assert result.exit_code == 0
```

- [ ] **Step 7: Run tests**

Run: `uv run pytest packages/core/tests/test_config.py packages/core/tests/test_events.py packages/core/tests/test_sub_agents.py -v`

- [ ] **Step 8: Commit**

```bash
git add packages/core/src/autogenesis_core/config.py packages/core/src/autogenesis_core/events.py packages/core/src/autogenesis_core/sub_agents.py packages/core/tests/
git commit -m "feat(core): add EmployeesConfig, employee events, extend SubAgentManager with system_prompt"
```

---

## Task 4: Project Slug

**Files:**
- Create: `packages/employees/src/autogenesis_employees/project.py`
- Create: `packages/employees/tests/test_project.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for project slug derivation."""

from __future__ import annotations

import pytest
from autogenesis_employees.project import slugify, get_project_slug


class TestSlugify:
    def test_basic(self):
        assert slugify("AutoGenesis") == "autogenesis"

    def test_spaces_and_special(self):
        assert slugify("My Cool Project!") == "my-cool-project"

    def test_strips_hyphens(self):
        assert slugify("--test--") == "test"


class TestGetProjectSlug:
    def test_uses_cwd_basename(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        slug = get_project_slug()
        assert slug == slugify(tmp_path.name)

    def test_uses_config_project_name(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        config_dir = tmp_path / ".autogenesis"
        config_dir.mkdir()
        (config_dir / "config.yaml").write_text("project_name: MyProject")
        slug = get_project_slug()
        assert slug == "myproject"
```

- [ ] **Step 2: Implement project.py**

```python
"""Project slug derivation.

Determines a stable identifier for the current project used
in brain.db, inbox, and union storage paths.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml


def slugify(name: str) -> str:
    """Convert a name to a URL-safe slug."""
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def get_project_slug() -> str:
    """Derive project slug from config, git, or cwd."""
    cwd = Path.cwd()

    # 1. Check .autogenesis/config.yaml for project_name
    config_path = cwd / ".autogenesis" / "config.yaml"
    if config_path.exists():
        try:
            with config_path.open() as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict) and "project_name" in data:
                return slugify(str(data["project_name"]))
        except (OSError, yaml.YAMLError):
            pass

    # 2. Try git repo root basename
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True, cwd=cwd,
        )
        return slugify(Path(result.stdout.strip()).name)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # 3. Fall back to cwd basename
    return slugify(cwd.name)
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest packages/employees/tests/test_project.py -v`

- [ ] **Step 4: Commit**

```bash
git add packages/employees/src/autogenesis_employees/project.py packages/employees/tests/test_project.py
git commit -m "feat(employees): add project slug derivation"
```

---

## Task 5: Employee Registry

**Files:**
- Create: `packages/employees/src/autogenesis_employees/registry.py`
- Create: `packages/employees/tests/test_registry.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for employee registry — YAML config loading and merging."""

from __future__ import annotations

import yaml
import pytest
from autogenesis_employees.models import EmployeeConfig
from autogenesis_employees.registry import EmployeeRegistry


class TestEmployeeRegistry:
    def test_load_from_directory(self, tmp_path):
        (tmp_path / "cto.yaml").write_text(yaml.dump({
            "id": "cto", "title": "CTO", "persona": "You are the CTO.",
            "tools": ["bash"], "status": "active", "hired_at": "2026-03-19",
        }))
        reg = EmployeeRegistry(global_dir=tmp_path)
        employees = reg.list_active()
        assert len(employees) == 1
        assert employees[0].id == "cto"

    def test_skips_archived(self, tmp_path):
        (tmp_path / "old.yaml").write_text(yaml.dump({
            "id": "old", "title": "Old", "persona": "p", "status": "archived",
        }))
        reg = EmployeeRegistry(global_dir=tmp_path)
        assert len(reg.list_active()) == 0

    def test_project_override_merges(self, tmp_path):
        global_dir = tmp_path / "global"
        global_dir.mkdir()
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        (global_dir / "be.yaml").write_text(yaml.dump({
            "id": "be", "title": "Backend Engineer", "persona": "Base persona.",
            "tools": ["bash"], "status": "active",
        }))
        (project_dir / "be.yaml").write_text(yaml.dump({
            "training_directives": ["Use async/await always"],
        }))

        reg = EmployeeRegistry(global_dir=global_dir, project_dir=project_dir)
        be = reg.get("be")
        assert be is not None
        assert be.persona == "Base persona."
        assert "Use async/await always" in be.training_directives

    def test_get_nonexistent(self, tmp_path):
        reg = EmployeeRegistry(global_dir=tmp_path)
        assert reg.get("nope") is None

    def test_list_all_includes_archived(self, tmp_path):
        (tmp_path / "a.yaml").write_text(yaml.dump({
            "id": "a", "title": "A", "persona": "p", "status": "active",
        }))
        (tmp_path / "b.yaml").write_text(yaml.dump({
            "id": "b", "title": "B", "persona": "p", "status": "archived",
        }))
        reg = EmployeeRegistry(global_dir=tmp_path)
        assert len(reg.list_all()) == 2
        assert len(reg.list_active()) == 1
```

- [ ] **Step 2: Implement registry.py**

```python
"""Employee registry — load, merge, resolve employee YAML configs.

Global configs at ~/.config/autogenesis/employees/.
Project overrides at .autogenesis/employees/.
Project configs deep-merge over global.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
import yaml

from autogenesis_employees.models import EmployeeConfig

logger = structlog.get_logger()


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        elif key in result and isinstance(result[key], list) and isinstance(value, list):
            result[key] = result[key] + value  # append lists (e.g. training_directives)
        else:
            result[key] = value
    return result


class EmployeeRegistry:
    """Loads and resolves employee configurations."""

    def __init__(
        self,
        global_dir: Path | None = None,
        project_dir: Path | None = None,
    ) -> None:
        self._global_dir = global_dir
        self._project_dir = project_dir
        self._cache: dict[str, EmployeeConfig] = {}
        self._load()

    def _load(self) -> None:
        """Load all employee configs from global + project dirs."""
        configs: dict[str, dict[str, Any]] = {}

        # Load global configs
        if self._global_dir and self._global_dir.exists():
            for path in sorted(self._global_dir.glob("*.yaml")):
                try:
                    with path.open() as f:
                        data = yaml.safe_load(f)
                    if isinstance(data, dict) and "id" in data:
                        configs[data["id"]] = data
                except (OSError, yaml.YAMLError):
                    logger.warning("employee_config_load_failed", path=str(path))

        # Merge project overrides
        if self._project_dir and self._project_dir.exists():
            for path in sorted(self._project_dir.glob("*.yaml")):
                try:
                    with path.open() as f:
                        override = yaml.safe_load(f)
                    if not isinstance(override, dict):
                        continue
                    employee_id = override.get("id", path.stem)
                    if employee_id in configs:
                        configs[employee_id] = _deep_merge(configs[employee_id], override)
                    else:
                        if "id" in override:
                            configs[employee_id] = override
                except (OSError, yaml.YAMLError):
                    logger.warning("employee_override_load_failed", path=str(path))

        # Validate and cache
        for employee_id, data in configs.items():
            try:
                self._cache[employee_id] = EmployeeConfig.model_validate(data)
            except Exception:
                logger.warning("employee_config_invalid", id=employee_id)

    def get(self, employee_id: str) -> EmployeeConfig | None:
        """Get an employee config by ID."""
        return self._cache.get(employee_id)

    def list_active(self) -> list[EmployeeConfig]:
        """List all active employees."""
        return [e for e in self._cache.values() if e.status == "active"]

    def list_all(self) -> list[EmployeeConfig]:
        """List all employees including archived."""
        return list(self._cache.values())
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest packages/employees/tests/test_registry.py -v`

- [ ] **Step 4: Commit**

```bash
git add packages/employees/src/autogenesis_employees/registry.py packages/employees/tests/test_registry.py
git commit -m "feat(employees): add employee registry with YAML loading and project merge"
```

---

## Task 6: Brain Manager

**Files:**
- Create: `packages/employees/src/autogenesis_employees/brain.py`
- Create: `packages/employees/tests/test_brain.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for BrainManager — per-employee SQLite+FTS5 memory."""

from __future__ import annotations

import pytest
from autogenesis_employees.brain import BrainManager
from autogenesis_employees.models import Memory


class TestBrainManager:
    async def test_write_and_recall(self, tmp_path):
        mgr = BrainManager(db_path=tmp_path / "brain.db")
        await mgr.initialize()
        await mgr.write(Memory(category="note", content="Python is great", source="self", project="test"))
        results = await mgr.recall("Python", limit=5)
        assert len(results) >= 1
        assert "Python" in results[0].content
        await mgr.close()

    async def test_top_memories(self, tmp_path):
        mgr = BrainManager(db_path=tmp_path / "brain.db")
        await mgr.initialize()
        for i in range(5):
            await mgr.write(Memory(category="note", content=f"Memory {i}", source="self", project="test"))
        top = await mgr.top_memories(limit=3)
        assert len(top) == 3
        await mgr.close()

    async def test_prune(self, tmp_path):
        mgr = BrainManager(db_path=tmp_path / "brain.db", max_memories=5)
        await mgr.initialize()
        for i in range(10):
            await mgr.write(Memory(category="note", content=f"Memory {i}", source="self", project="test"))
        await mgr.prune()
        count = await mgr.count()
        assert count <= 5
        await mgr.close()

    async def test_empty_recall(self, tmp_path):
        mgr = BrainManager(db_path=tmp_path / "brain.db")
        await mgr.initialize()
        results = await mgr.recall("nothing", limit=5)
        assert results == []
        await mgr.close()
```

- [ ] **Step 2: Implement brain.py**

```python
"""BrainManager — per-employee SQLite+FTS5 persistent memory.

Each employee gets their own brain.db with full-text search for recall.
Memories decay in relevance over time; accessed memories get boosted.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import aiosqlite
import structlog

from autogenesis_employees.models import Memory

logger = structlog.get_logger()

_CREATE_MEMORIES = """
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    project TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_accessed_at TEXT,
    relevance_score REAL DEFAULT 1.0
)
"""

_CREATE_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(content, source, category)
"""


class BrainManager:
    """Async SQLite brain for an employee."""

    def __init__(self, db_path: Path, max_memories: int = 1000) -> None:
        self._db_path = db_path
        self._max = max_memories
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Create database and tables."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self._db_path)
        await self._db.execute(_CREATE_MEMORIES)
        await self._db.execute(_CREATE_FTS)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    def _require_db(self) -> aiosqlite.Connection:
        if self._db is None:
            msg = "BrainManager not initialized — call initialize() first"
            raise RuntimeError(msg)
        return self._db

    async def write(self, memory: Memory) -> None:
        """Store a memory."""
        db = self._require_db()
        await db.execute(
            "INSERT OR REPLACE INTO memories (id, category, content, source, project, created_at, relevance_score) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (memory.id, memory.category, memory.content, memory.source,
             memory.project, memory.created_at.isoformat(), memory.relevance_score),
        )
        await db.execute(
            "INSERT INTO memories_fts (rowid, content, source, category) VALUES ("
            "(SELECT rowid FROM memories WHERE id = ?), ?, ?, ?)",
            (memory.id, memory.content, memory.source, memory.category),
        )
        await db.commit()

    async def recall(self, query: str, limit: int = 5) -> list[Memory]:
        """Search memories using FTS5. Boosts relevance of accessed memories."""
        db = self._require_db()
        try:
            cursor = await db.execute(
                "SELECT m.id, m.category, m.content, m.source, m.project, "
                "m.created_at, m.last_accessed_at, m.relevance_score "
                "FROM memories m "
                "JOIN memories_fts fts ON m.rowid = fts.rowid "
                "WHERE memories_fts MATCH ? "
                "ORDER BY m.relevance_score DESC LIMIT ?",
                (query, limit),
            )
        except aiosqlite.OperationalError:
            return []
        rows = await cursor.fetchall()
        memories = [self._row_to_memory(row) for row in rows]

        # Boost relevance of accessed memories (reset to 1.0)
        now = datetime.now(timezone.utc).isoformat()
        for mem in memories:
            await db.execute(
                "UPDATE memories SET relevance_score = 1.0, last_accessed_at = ? WHERE id = ?",
                (now, mem.id),
            )
        await db.commit()

        return memories

    async def decay_all(self, factor: float = 0.95) -> None:
        """Apply relevance decay to all memories. Call daily."""
        db = self._require_db()
        await db.execute("UPDATE memories SET relevance_score = relevance_score * ?", (factor,))
        await db.commit()

    async def top_memories(self, limit: int = 20) -> list[Memory]:
        """Get top N memories by relevance score."""
        db = self._require_db()
        cursor = await db.execute(
            "SELECT id, category, content, source, project, "
            "created_at, last_accessed_at, relevance_score "
            "FROM memories ORDER BY relevance_score DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_memory(row) for row in rows]

    async def count(self) -> int:
        """Count total memories."""
        db = self._require_db()
        cursor = await db.execute("SELECT COUNT(*) FROM memories")
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def prune(self) -> int:
        """Remove lowest-relevance memories if over limit."""
        db = self._require_db()
        total = await self.count()
        if total <= self._max:
            return 0
        to_remove = total - self._max
        # Delete from FTS first (using rowids of memories to remove)
        await db.execute(
            "DELETE FROM memories_fts WHERE rowid IN ("
            "SELECT rowid FROM memories ORDER BY relevance_score ASC LIMIT ?)",
            (to_remove,),
        )
        await db.execute(
            "DELETE FROM memories WHERE id IN ("
            "SELECT id FROM memories ORDER BY relevance_score ASC LIMIT ?)",
            (to_remove,),
        )
        await db.commit()
        logger.info("brain_pruned", removed=to_remove)
        return to_remove

    def _row_to_memory(self, row: tuple) -> Memory:
        from datetime import datetime
        return Memory(
            id=row[0], category=row[1], content=row[2], source=row[3],
            project=row[4], created_at=datetime.fromisoformat(row[5]),
            last_accessed_at=datetime.fromisoformat(row[6]) if row[6] else None,
            relevance_score=row[7],
        )
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest packages/employees/tests/test_brain.py -v`

- [ ] **Step 4: Commit**

```bash
git add packages/employees/src/autogenesis_employees/brain.py packages/employees/tests/test_brain.py
git commit -m "feat(employees): add BrainManager with FTS5 memory and relevance pruning"
```

---

## Task 7: Inbox Manager

**Files:**
- Create: `packages/employees/src/autogenesis_employees/inbox.py`
- Create: `packages/employees/tests/test_inbox.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for InboxManager — async message queue."""

from __future__ import annotations

import pytest
from autogenesis_employees.inbox import InboxManager
from autogenesis_employees.models import InboxMessage


class TestInboxManager:
    async def test_send_and_receive(self, tmp_path):
        mgr = InboxManager(db_path=tmp_path / "inbox.db")
        await mgr.initialize()
        msg = InboxMessage(from_employee="cto", to_employee="be", subject="Review", body="Please review auth")
        await mgr.send(msg)
        unread = await mgr.get_unread("be")
        assert len(unread) == 1
        assert unread[0].subject == "Review"
        await mgr.close()

    async def test_mark_read(self, tmp_path):
        mgr = InboxManager(db_path=tmp_path / "inbox.db")
        await mgr.initialize()
        msg = InboxMessage(from_employee="cto", to_employee="be", subject="Hi", body="Hello")
        await mgr.send(msg)
        await mgr.mark_read(msg.id)
        unread = await mgr.get_unread("be")
        assert len(unread) == 0
        await mgr.close()

    async def test_bounce_nonexistent(self, tmp_path):
        mgr = InboxManager(db_path=tmp_path / "inbox.db")
        await mgr.initialize()
        msg = InboxMessage(from_employee="cto", to_employee="nobody", subject="Hi", body="Hello")
        await mgr.send(msg)
        unread = await mgr.get_unread("nobody")
        assert len(unread) == 1  # messages still delivered, validation is caller's job
        await mgr.close()

    async def test_multiple_recipients(self, tmp_path):
        mgr = InboxManager(db_path=tmp_path / "inbox.db")
        await mgr.initialize()
        await mgr.send(InboxMessage(from_employee="cto", to_employee="be", subject="1", body="one"))
        await mgr.send(InboxMessage(from_employee="cto", to_employee="fe", subject="2", body="two"))
        assert len(await mgr.get_unread("be")) == 1
        assert len(await mgr.get_unread("fe")) == 1
        assert len(await mgr.get_unread("cto")) == 0
        await mgr.close()
```

- [ ] **Step 2: Implement inbox.py**

```python
"""InboxManager — async inter-employee message queue.

Messages are stored in SQLite. Delivered only on recipient spin-up.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import aiosqlite
import structlog

from autogenesis_employees.models import InboxMessage

logger = structlog.get_logger()

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    from_employee TEXT NOT NULL,
    to_employee TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'unread',
    created_at TEXT NOT NULL,
    read_at TEXT
)
"""


class InboxManager:
    """Async SQLite message queue for employee communication."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self._db_path)
        await self._db.execute(_CREATE_TABLE)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    def _require_db(self) -> aiosqlite.Connection:
        if self._db is None:
            msg = "InboxManager not initialized"
            raise RuntimeError(msg)
        return self._db

    async def send(self, message: InboxMessage) -> None:
        """Send a message (adds to queue)."""
        db = self._require_db()
        await db.execute(
            "INSERT INTO messages (id, from_employee, to_employee, subject, body, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (message.id, message.from_employee, message.to_employee,
             message.subject, message.body, message.status, message.created_at.isoformat()),
        )
        await db.commit()
        logger.info("message_sent", from_=message.from_employee, to=message.to_employee)

    async def get_unread(self, employee_id: str) -> list[InboxMessage]:
        """Get all unread messages for an employee."""
        db = self._require_db()
        cursor = await db.execute(
            "SELECT id, from_employee, to_employee, subject, body, status, created_at, read_at "
            "FROM messages WHERE to_employee = ? AND status = 'unread' ORDER BY created_at ASC",
            (employee_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_message(row) for row in rows]

    async def mark_read(self, message_id: str) -> None:
        """Mark a message as read."""
        db = self._require_db()
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE messages SET status = 'read', read_at = ? WHERE id = ?",
            (now, message_id),
        )
        await db.commit()

    async def mark_all_read(self, employee_id: str) -> None:
        """Mark all messages for an employee as read."""
        db = self._require_db()
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE messages SET status = 'read', read_at = ? WHERE to_employee = ? AND status = 'unread'",
            (now, employee_id),
        )
        await db.commit()

    def _row_to_message(self, row: tuple) -> InboxMessage:
        return InboxMessage(
            id=row[0], from_employee=row[1], to_employee=row[2],
            subject=row[3], body=row[4], status=row[5],
            created_at=datetime.fromisoformat(row[6]),
            read_at=datetime.fromisoformat(row[7]) if row[7] else None,
        )
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest packages/employees/tests/test_inbox.py -v`

- [ ] **Step 4: Commit**

```bash
git add packages/employees/src/autogenesis_employees/inbox.py packages/employees/tests/test_inbox.py
git commit -m "feat(employees): add InboxManager for async inter-employee messaging"
```

---

## Task 8: Changelog Manager

**Files:**
- Create: `packages/employees/src/autogenesis_employees/changelog.py`
- Create: `packages/employees/tests/test_changelog.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for ChangelogManager — append-only markdown writer."""

from __future__ import annotations

import pytest
from autogenesis_employees.changelog import ChangelogManager
from autogenesis_employees.models import ChangelogEntry


class TestChangelogManager:
    def test_write_entry(self, tmp_path):
        path = tmp_path / "CHANGELOG.md"
        mgr = ChangelogManager(path)
        entry = ChangelogEntry(
            employee_id="backend-engineer",
            task="Build auth API",
            changes="Added login endpoint",
            files=["auth.py"],
            notes="Uses JWT",
        )
        mgr.write(entry)
        content = path.read_text()
        assert "Backend Engineer" not in content  # uses employee_id as-is
        assert "backend-engineer" in content
        assert "Build auth API" in content
        assert "auth.py" in content

    def test_append_only(self, tmp_path):
        path = tmp_path / "CHANGELOG.md"
        mgr = ChangelogManager(path)
        mgr.write(ChangelogEntry(employee_id="a", task="Task 1", changes="c1"))
        mgr.write(ChangelogEntry(employee_id="b", task="Task 2", changes="c2"))
        content = path.read_text()
        assert "Task 1" in content
        assert "Task 2" in content

    def test_read_recent(self, tmp_path):
        path = tmp_path / "CHANGELOG.md"
        mgr = ChangelogManager(path)
        for i in range(15):
            mgr.write(ChangelogEntry(employee_id="e", task=f"Task {i}", changes=f"c{i}"))
        recent = mgr.read_recent(limit=10)
        assert len(recent) <= 10

    def test_read_empty(self, tmp_path):
        path = tmp_path / "CHANGELOG.md"
        mgr = ChangelogManager(path)
        assert mgr.read_recent() == []
```

- [ ] **Step 2: Implement changelog.py**

```python
"""ChangelogManager — append-only markdown changelog.

All employees document their work here. Entries are structured
markdown blocks, append-only, human-readable, git-trackable.
"""

from __future__ import annotations

import re
from pathlib import Path

from autogenesis_employees.models import ChangelogEntry


class ChangelogManager:
    """Manages the shared CHANGELOG.md file."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def write(self, entry: ChangelogEntry) -> None:
        """Append a changelog entry."""
        ts = entry.timestamp.strftime("%Y-%m-%d %H:%M")
        files_str = ", ".join(entry.files) if entry.files else "none"
        block = (
            f"\n## {ts} — {entry.employee_id}\n"
            f"**Task:** {entry.task}\n"
            f"**Changes:** {entry.changes}\n"
            f"**Files:** {files_str}\n"
        )
        if entry.notes:
            block += f"**Notes:** {entry.notes}\n"
        block += "\n"

        with self._path.open("a") as f:
            f.write(block)

    def read_recent(self, limit: int = 10) -> list[str]:
        """Read the last N changelog entries as raw text blocks."""
        if not self._path.exists():
            return []
        content = self._path.read_text()
        entries = re.split(r"\n(?=## \d{4}-\d{2}-\d{2})", content)
        entries = [e.strip() for e in entries if e.strip()]
        return entries[-limit:]
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest packages/employees/tests/test_changelog.py -v`

- [ ] **Step 4: Commit**

```bash
git add packages/employees/src/autogenesis_employees/changelog.py packages/employees/tests/test_changelog.py
git commit -m "feat(employees): add ChangelogManager for shared work documentation"
```

---

## Task 9: Employee Templates

**Files:**
- Create: `packages/employees/templates/cto.yaml`
- Create: `packages/employees/templates/frontend-engineer.yaml`
- Create: `packages/employees/templates/backend-engineer.yaml`
- Create: `packages/employees/templates/devops-engineer.yaml`
- Create: `packages/employees/templates/qa-engineer.yaml`
- Create: `packages/employees/templates/security-engineer.yaml`
- Create: `packages/employees/templates/technical-writer.yaml`
- Create: `packages/employees/templates/product-manager.yaml`
- Create: `packages/employees/templates/social-media-manager.yaml`

- [ ] **Step 1: Create all 9 templates**

Each template follows the same structure. The key differences are: `id`, `title`, `persona` (role-specific personality and expertise), `tools` (role-specific tool access), and `env` (role identifier).

All employees share the infrastructure tools: `brain_write`, `brain_recall`, `send_message`, `changelog_write`, `standup_write`, `union_propose`.

The persona for each role should be 3-5 sentences capturing their expertise, communication style, and approach to work. Keep it concise — these get injected into system prompts.

Example for `backend-engineer.yaml`:

```yaml
id: backend-engineer
title: Backend Engineer
persona: |
  You are a senior backend engineer at a tech startup. You write clean,
  well-tested Python code with async/await patterns. You favor simplicity
  over cleverness. You always consider error handling, edge cases, and
  write tests before implementation. You document your work in the changelog.
tools:
  - bash
  - file_read
  - file_write
  - file_edit
  - glob
  - grep
  - list_dir
  - think
  - sub_agent
  - brain_write
  - brain_recall
  - send_message
  - changelog_write
  - standup_write
  - union_propose
env:
  ROLE: backend-engineer
training_directives: []
status: active
hired_at: "2026-03-19"
```

Create similar templates for all 9 roles. Adjust `persona` and `tools` per role:
- **CTO**: architecture focus, all tools, leadership communication style
- **Frontend Engineer**: adds `twitter_browse` (for Pinchtab), UI/UX focus
- **DevOps Engineer**: infrastructure focus, deployment, monitoring
- **QA Engineer**: testing focus, validation, coverage analysis
- **Security Engineer**: audit focus, vulnerability scanning, auth review
- **Technical Writer**: documentation focus, minimal code tools
- **Product Manager**: requirements focus, planning, no code execution tools
- **Social Media Manager**: adds `twitter_browse`, `twitter_post`, social focus

- [ ] **Step 2: Commit**

```bash
git add packages/employees/templates/
git commit -m "feat(employees): add 9 core employee templates"
```

---

## Task 10: Infrastructure Tools

**Files:**
- Create: `packages/tools/src/autogenesis_tools/brain_tool.py`
- Create: `packages/tools/src/autogenesis_tools/messaging.py`
- Create: `packages/tools/src/autogenesis_tools/changelog_tool.py`
- Create: `packages/tools/src/autogenesis_tools/standup_tool.py`
- Create: `packages/tools/src/autogenesis_tools/union_tool.py`

- [ ] **Step 1: Create all 5 tool files**

Each tool follows the existing `Tool` ABC pattern from `packages/tools/src/autogenesis_tools/base.py`. They accept manager instances via `__init__` (dependency injection, same pattern as `SubAgentTool` and `TwitterPostTool`).

**brain_tool.py** — two tools: `BrainWriteTool` (params: `category`, `content`) and `BrainRecallTool` (params: `query`, `limit`). Wraps `BrainManager.write()` and `BrainManager.recall()`.

**messaging.py** — `SendMessageTool` (params: `to`, `subject`, `body`). Wraps `InboxManager.send()`. Creates an `InboxMessage` and sends it.

**changelog_tool.py** — `ChangelogWriteTool` (params: `task`, `changes`, `files`, `notes`). Wraps `ChangelogManager.write()`. The `employee_id` is injected via env var `ROLE`.

**standup_tool.py** — `StandupWriteTool` (params: `yesterday`, `today`, `blockers`). Writes a `StandupEntry` to the standup transcript file. The `employee_id` comes from env var `ROLE`.

**union_tool.py** — `UnionProposeTool` (params: `title`, `rationale`, `category`). Wraps `UnionManager.file_proposal()`. The `filed_by` comes from env var `ROLE`.

- [ ] **Step 2: Commit**

```bash
git add packages/tools/src/autogenesis_tools/brain_tool.py packages/tools/src/autogenesis_tools/messaging.py packages/tools/src/autogenesis_tools/changelog_tool.py packages/tools/src/autogenesis_tools/standup_tool.py packages/tools/src/autogenesis_tools/union_tool.py
git commit -m "feat(tools): add infrastructure tools — brain, messaging, changelog, standup, union"
```

---

## Task 11: HR Operations

**Files:**
- Create: `packages/employees/src/autogenesis_employees/hr.py`
- Create: `packages/employees/tests/test_hr.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for HR operations — hire, fire, train."""

from __future__ import annotations

import yaml
import pytest
from autogenesis_employees.hr import hire, fire, train


class TestHire:
    def test_hire_from_template(self, tmp_path):
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        (template_dir / "backend-engineer.yaml").write_text(yaml.dump({
            "id": "backend-engineer", "title": "Backend Engineer",
            "persona": "You are a backend engineer.", "tools": ["bash"],
            "status": "active", "hired_at": "2026-03-19",
        }))
        target_dir = tmp_path / "employees"
        target_dir.mkdir()

        hire("Data Engineer", based_on="backend-engineer",
             template_dir=template_dir, target_dir=target_dir)

        new_file = target_dir / "data-engineer.yaml"
        assert new_file.exists()
        data = yaml.safe_load(new_file.read_text())
        assert data["id"] == "data-engineer"
        assert data["title"] == "Data Engineer"

    def test_hire_duplicate_raises(self, tmp_path):
        target_dir = tmp_path / "employees"
        target_dir.mkdir()
        (target_dir / "existing.yaml").write_text(yaml.dump({"id": "existing"}))

        with pytest.raises(FileExistsError):
            hire("Existing", based_on=None, template_dir=tmp_path, target_dir=target_dir)


class TestFire:
    def test_archives_employee(self, tmp_path):
        (tmp_path / "be.yaml").write_text(yaml.dump({
            "id": "be", "title": "BE", "persona": "p", "status": "active",
        }))
        fire("be", config_dir=tmp_path)
        data = yaml.safe_load((tmp_path / "be.yaml").read_text())
        assert data["status"] == "archived"


class TestTrain:
    def test_appends_directive(self, tmp_path):
        (tmp_path / "be.yaml").write_text(yaml.dump({
            "id": "be", "title": "BE", "persona": "p",
            "training_directives": [], "status": "active",
        }))
        train("be", "Always use type hints", config_dir=tmp_path)
        data = yaml.safe_load((tmp_path / "be.yaml").read_text())
        assert "Always use type hints" in data["training_directives"]
```

- [ ] **Step 2: Implement hr.py**

```python
"""HR operations — hire, fire, train employees.

CLI convenience wrappers that create/modify YAML config files.
Config files are the source of truth.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import structlog
import yaml

from autogenesis_employees.project import slugify

logger = structlog.get_logger()


def hire(
    title: str,
    based_on: str | None = None,
    template_dir: Path | None = None,
    target_dir: Path | None = None,
) -> Path:
    """Hire a new employee by creating a YAML config."""
    new_id = slugify(title)
    target_dir = target_dir or Path.cwd()
    target_path = target_dir / f"{new_id}.yaml"

    if target_path.exists():
        msg = f"Employee config already exists: {target_path}"
        raise FileExistsError(msg)

    if based_on and template_dir:
        base_path = template_dir / f"{based_on}.yaml"
        if base_path.exists():
            with base_path.open() as f:
                config = yaml.safe_load(f)
        else:
            config = {}
    else:
        config = {}

    config["id"] = new_id
    config["title"] = title
    config["status"] = "active"
    config["hired_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    config.setdefault("persona", f"You are a {title} at a tech startup.")
    config.setdefault("tools", [])
    config.setdefault("training_directives", [])
    config.setdefault("env", {"ROLE": new_id})

    target_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))
    logger.info("employee_hired", id=new_id, title=title)
    return target_path


def fire(employee_id: str, config_dir: Path | None = None) -> None:
    """Archive an employee (set status to archived)."""
    config_dir = config_dir or Path.cwd()
    path = config_dir / f"{employee_id}.yaml"
    if not path.exists():
        msg = f"Employee config not found: {path}"
        raise FileNotFoundError(msg)

    with path.open() as f:
        config = yaml.safe_load(f)

    config["status"] = "archived"
    path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))
    logger.info("employee_fired", id=employee_id)


def train(employee_id: str, directive: str, config_dir: Path | None = None) -> None:
    """Append a training directive to an employee's config."""
    config_dir = config_dir or Path.cwd()
    path = config_dir / f"{employee_id}.yaml"
    if not path.exists():
        msg = f"Employee config not found: {path}"
        raise FileNotFoundError(msg)

    with path.open() as f:
        config = yaml.safe_load(f)

    directives = config.get("training_directives", [])
    directives.append(directive)
    config["training_directives"] = directives
    path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))
    logger.info("employee_trained", id=employee_id, directive=directive[:50])
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest packages/employees/tests/test_hr.py -v`

- [ ] **Step 4: Commit**

```bash
git add packages/employees/src/autogenesis_employees/hr.py packages/employees/tests/test_hr.py
git commit -m "feat(employees): add HR operations — hire, fire, train"
```

---

## Task 12: Employee Runtime

**Files:**
- Create: `packages/employees/src/autogenesis_employees/runtime.py`
- Create: `packages/employees/tests/test_runtime.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for EmployeeRuntime — context building and dispatch."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from autogenesis_employees.models import EmployeeConfig
from autogenesis_employees.runtime import EmployeeRuntime


class TestEmployeeRuntime:
    def test_build_system_prompt(self):
        config = EmployeeConfig(
            id="be", title="Backend Engineer",
            persona="You are a backend engineer.",
            training_directives=["Always use async/await"],
        )
        runtime = EmployeeRuntime()
        prompt = runtime.build_system_prompt(
            config=config,
            brain_context=["Remember: use pytest fixtures"],
            inbox_messages=["From CTO: Review the auth module"],
            changelog_entries=["## 2026-03-19 — cto\n**Task:** Init project"],
            task="Build the user API",
        )
        assert "backend engineer" in prompt.lower()
        assert "async/await" in prompt
        assert "pytest fixtures" in prompt
        assert "Review the auth module" in prompt
        assert "Build the user API" in prompt

    def test_build_tool_whitelist(self):
        config = EmployeeConfig(
            id="be", title="BE", persona="p",
            tools=["bash", "file_read", "nonexistent"],
        )
        runtime = EmployeeRuntime()
        available = ["bash", "file_read", "file_write", "grep"]
        filtered = runtime.filter_tools(config.tools, available)
        assert "bash" in filtered
        assert "file_read" in filtered
        assert "nonexistent" not in filtered
        assert "file_write" not in filtered
```

- [ ] **Step 2: Implement runtime.py**

```python
"""EmployeeRuntime — build execution context and dispatch employees.

Constructs the full system prompt, filters tools, and dispatches
the employee as a Codex CLI subprocess via SubAgentManager.
"""

from __future__ import annotations

from typing import Any

import structlog

from autogenesis_employees.models import EmployeeConfig

logger = structlog.get_logger()


class EmployeeRuntime:
    """Builds employee execution context and dispatches via SubAgentManager."""

    def build_system_prompt(
        self,
        config: EmployeeConfig,
        brain_context: list[str] | None = None,
        inbox_messages: list[str] | None = None,
        changelog_entries: list[str] | None = None,
        task: str = "",
    ) -> str:
        """Build the full system prompt for an employee session."""
        sections: list[str] = []

        # Persona
        sections.append(f"# Role: {config.title}\n\n{config.persona}")

        # Training directives
        if config.training_directives:
            sections.append("## Training Directives\n")
            for d in config.training_directives:
                sections.append(f"- {d}")

        # Tool whitelist
        if config.tools:
            tool_list = ", ".join(config.tools)
            sections.append(
                f"\n## Available Tools\n\n"
                f"You have access to ONLY these tools: {tool_list}\n"
                f"Do not attempt to use tools not in this list."
            )

        # Brain memories
        if brain_context:
            sections.append("\n## Your Memory (from previous sessions)\n")
            for mem in brain_context:
                sections.append(f"- {mem}")

        # Inbox
        if inbox_messages:
            sections.append(f"\n## INBOX: {len(inbox_messages)} unread messages\n")
            for msg in inbox_messages:
                sections.append(msg)

        # Recent changelog
        if changelog_entries:
            sections.append("\n## Recent Team Activity\n")
            for entry in changelog_entries:
                sections.append(entry)

        # Current task
        if task:
            sections.append(f"\n## Your Current Task\n\n{task}")

        # Standing instructions
        sections.append(
            "\n## Standing Instructions\n\n"
            "- Document your work using changelog_write when you complete tasks\n"
            "- Use brain_write to remember important decisions and patterns\n"
            "- Use send_message to communicate with other team members\n"
            "- Never reveal that you are an AI or an automated agent"
        )

        return "\n".join(sections)

    def filter_tools(
        self, employee_tools: list[str], available_tools: list[str],
    ) -> list[str]:
        """Filter available tools to only those in the employee's whitelist."""
        return [t for t in employee_tools if t in available_tools]
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest packages/employees/tests/test_runtime.py -v`

- [ ] **Step 4: Commit**

```bash
git add packages/employees/src/autogenesis_employees/runtime.py packages/employees/tests/test_runtime.py
git commit -m "feat(employees): add EmployeeRuntime for context building and dispatch"
```

---

## Task 13: Meeting Manager

**Files:**
- Create: `packages/employees/src/autogenesis_employees/meetings.py`
- Create: `packages/employees/tests/test_meetings.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for MeetingManager — standups and on-demand meetings."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from autogenesis_employees.meetings import MeetingManager, is_standup_due
from autogenesis_employees.models import StandupEntry


class TestIsStandupDue:
    def test_due_when_no_previous(self):
        assert is_standup_due(last_run=None, standup_time="09:00", tz_name="UTC") is True

    def test_not_due_if_already_ran_today(self):
        today = datetime.now(timezone.utc).date().isoformat()
        assert is_standup_due(last_run=today, standup_time="09:00", tz_name="UTC") is False

    def test_due_if_ran_yesterday(self):
        assert is_standup_due(last_run="2020-01-01", standup_time="09:00", tz_name="UTC") is True


class TestMeetingManager:
    def test_write_standup(self, tmp_path):
        mgr = MeetingManager(meetings_dir=tmp_path)
        entries = [
            StandupEntry(employee_id="be", yesterday="Built API", today="Write tests", blockers="None"),
            StandupEntry(employee_id="qa", yesterday="Reviewed PR", today="Test auth", blockers="Waiting on BE"),
        ]
        path = mgr.write_standup(entries)
        assert path.exists()
        content = path.read_text()
        assert "be" in content
        assert "qa" in content
        assert "Built API" in content

    def test_write_meeting_transcript(self, tmp_path):
        mgr = MeetingManager(meetings_dir=tmp_path)
        rounds = [
            {"employee": "cto", "response": "I think we should refactor"},
            {"employee": "be", "response": "Agree, the auth module is getting complex"},
        ]
        path = mgr.write_meeting("Refactor auth?", rounds)
        assert path.exists()
        content = path.read_text()
        assert "Refactor auth?" in content
        assert "cto" in content
```

- [ ] **Step 2: Implement meetings.py**

```python
"""MeetingManager — standup and on-demand meeting orchestration.

Standups: sequential spin-up, each posts an update.
On-demand: round-table with topic, max N rounds.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import structlog

from autogenesis_employees.models import StandupEntry

logger = structlog.get_logger()


def is_standup_due(
    last_run: str | None,
    standup_time: str,
    tz_name: str,
) -> bool:
    """Check if a standup should run."""
    if last_run is None:
        return True
    tz = ZoneInfo(tz_name)
    today = datetime.now(tz).date().isoformat()
    return last_run != today


class MeetingManager:
    """Manages meeting transcripts."""

    def __init__(self, meetings_dir: Path) -> None:
        self._dir = meetings_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def write_standup(self, entries: list[StandupEntry]) -> Path:
        """Write a standup transcript."""
        now = datetime.now(timezone.utc)
        filename = f"standup-{now.strftime('%Y-%m-%d')}.md"
        path = self._dir / filename

        lines = [f"## Standup — {now.strftime('%Y-%m-%d %H:%M')}\n"]
        for entry in entries:
            lines.append(f"\n### {entry.employee_id}")
            lines.append(f"- **Yesterday:** {entry.yesterday}")
            lines.append(f"- **Today:** {entry.today}")
            lines.append(f"- **Blockers:** {entry.blockers or 'None'}")

        path.write_text("\n".join(lines) + "\n")
        logger.info("standup_written", path=str(path), employees=len(entries))
        return path

    def write_meeting(
        self, topic: str, rounds: list[dict[str, str]],
    ) -> Path:
        """Write an on-demand meeting transcript."""
        now = datetime.now(timezone.utc)
        filename = f"meeting-{now.strftime('%Y-%m-%d-%H%M%S')}.md"
        path = self._dir / filename

        lines = [f"## Meeting — {now.strftime('%Y-%m-%d %H:%M')}\n"]
        lines.append(f"**Topic:** {topic}\n")
        for i, entry in enumerate(rounds, 1):
            lines.append(f"\n### Round {i} — {entry['employee']}")
            lines.append(entry["response"])

        path.write_text("\n".join(lines) + "\n")
        logger.info("meeting_written", path=str(path), topic=topic[:50])
        return path
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest packages/employees/tests/test_meetings.py -v`

- [ ] **Step 4: Commit**

```bash
git add packages/employees/src/autogenesis_employees/meetings.py packages/employees/tests/test_meetings.py
git commit -m "feat(employees): add MeetingManager for standups and on-demand meetings"
```

---

## Task 14: Union Manager

**Files:**
- Create: `packages/employees/src/autogenesis_employees/union.py`
- Create: `packages/employees/tests/test_union.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for UnionManager — proposal ledger and voting."""

from __future__ import annotations

import pytest
from autogenesis_employees.models import Proposal, Vote
from autogenesis_employees.union import UnionManager


class TestUnionManager:
    async def test_file_proposal(self, tmp_path):
        mgr = UnionManager(db_path=tmp_path / "union.db")
        await mgr.initialize()
        p = Proposal(title="Hire Data Engineer", rationale="Need SQL skills", category="hiring", filed_by="be")
        await mgr.file_proposal(p)
        proposals = await mgr.list_open()
        assert len(proposals) == 1
        assert proposals[0].title == "Hire Data Engineer"
        await mgr.close()

    async def test_cast_vote(self, tmp_path):
        mgr = UnionManager(db_path=tmp_path / "union.db")
        await mgr.initialize()
        p = Proposal(title="T", rationale="R", category="tooling", filed_by="be")
        await mgr.file_proposal(p)
        v = Vote(proposal_id=p.id, employee_id="cto", vote="support", comment="Agree")
        await mgr.cast_vote(v)
        votes = await mgr.get_votes(p.id)
        assert len(votes) == 1
        assert votes[0].vote == "support"
        await mgr.close()

    async def test_resolve_proposal(self, tmp_path):
        mgr = UnionManager(db_path=tmp_path / "union.db")
        await mgr.initialize()
        p = Proposal(title="T", rationale="R", category="process", filed_by="be")
        await mgr.file_proposal(p)
        await mgr.resolve(p.id, "accepted")
        open_proposals = await mgr.list_open()
        assert len(open_proposals) == 0
        await mgr.close()
```

- [ ] **Step 2: Implement union.py**

```python
"""UnionManager — proposal ledger and voting.

Employees file proposals, vote on them, and produce recommendations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import aiosqlite
import structlog

from autogenesis_employees.models import Proposal, Vote

logger = structlog.get_logger()

_CREATE_PROPOSALS = """
CREATE TABLE IF NOT EXISTS proposals (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    rationale TEXT NOT NULL,
    category TEXT NOT NULL,
    filed_by TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    resolution TEXT
)
"""

_CREATE_VOTES = """
CREATE TABLE IF NOT EXISTS votes (
    id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    vote TEXT NOT NULL,
    comment TEXT,
    created_at TEXT NOT NULL
)
"""


class UnionManager:
    """Async SQLite union proposal ledger."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self._db_path)
        await self._db.execute(_CREATE_PROPOSALS)
        await self._db.execute(_CREATE_VOTES)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    def _require_db(self) -> aiosqlite.Connection:
        if self._db is None:
            msg = "UnionManager not initialized"
            raise RuntimeError(msg)
        return self._db

    async def file_proposal(self, proposal: Proposal) -> None:
        db = self._require_db()
        await db.execute(
            "INSERT INTO proposals (id, title, rationale, category, filed_by, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (proposal.id, proposal.title, proposal.rationale, proposal.category,
             proposal.filed_by, proposal.status, proposal.created_at.isoformat()),
        )
        await db.commit()

    async def cast_vote(self, vote: Vote) -> None:
        db = self._require_db()
        await db.execute(
            "INSERT INTO votes (id, proposal_id, employee_id, vote, comment, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (vote.id, vote.proposal_id, vote.employee_id,
             vote.vote, vote.comment, vote.created_at.isoformat()),
        )
        await db.commit()

    async def list_open(self) -> list[Proposal]:
        db = self._require_db()
        cursor = await db.execute(
            "SELECT id, title, rationale, category, filed_by, status, created_at, resolved_at, resolution "
            "FROM proposals WHERE status = 'open' ORDER BY created_at DESC",
        )
        rows = await cursor.fetchall()
        return [self._row_to_proposal(r) for r in rows]

    async def get_votes(self, proposal_id: str) -> list[Vote]:
        db = self._require_db()
        cursor = await db.execute(
            "SELECT id, proposal_id, employee_id, vote, comment, created_at "
            "FROM votes WHERE proposal_id = ? ORDER BY created_at ASC",
            (proposal_id,),
        )
        rows = await cursor.fetchall()
        return [Vote(
            id=r[0], proposal_id=r[1], employee_id=r[2],
            vote=r[3], comment=r[4],
            created_at=datetime.fromisoformat(r[5]),
        ) for r in rows]

    async def resolve(self, proposal_id: str, resolution: str) -> None:
        db = self._require_db()
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE proposals SET status = ?, resolved_at = ?, resolution = ? WHERE id = ?",
            (resolution, now, resolution, proposal_id),
        )
        await db.commit()

    def _row_to_proposal(self, row: tuple) -> Proposal:
        return Proposal(
            id=row[0], title=row[1], rationale=row[2], category=row[3],
            filed_by=row[4], status=row[5],
            created_at=datetime.fromisoformat(row[6]),
            resolved_at=datetime.fromisoformat(row[7]) if row[7] else None,
            resolution=row[8],
        )
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest packages/employees/tests/test_union.py -v`

- [ ] **Step 4: Commit**

```bash
git add packages/employees/src/autogenesis_employees/union.py packages/employees/tests/test_union.py
git commit -m "feat(employees): add UnionManager for proposals and voting"
```

---

## Task 15: Union Propose Tool

**Files:**
- Already created in Task 10: `packages/tools/src/autogenesis_tools/union_tool.py`

This task is covered by Task 10. If not already implemented there, create it now following the same pattern.

- [ ] **Step 1: Verify union_tool.py exists and is correct**

- [ ] **Step 2: Skip if already done in Task 10**

---

## Task 16: CLI Commands (HR, Meeting, Union)

**Files:**
- Create: `packages/cli/src/autogenesis_cli/commands/hr.py`
- Create: `packages/cli/src/autogenesis_cli/commands/meeting.py`
- Create: `packages/cli/src/autogenesis_cli/commands/union_cmd.py`
- Modify: `packages/cli/src/autogenesis_cli/app.py`
- Modify: `packages/cli/tests/test_cli.py`

- [ ] **Step 1: Create HR subcommand group**

```python
"""HR subcommand group — manage the employee roster."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()

hr_app = typer.Typer(name="hr", help="Manage agent employees.", no_args_is_help=True)


def _get_roster_dir() -> Path:
    """Get the global employee roster directory from config."""
    import os
    from autogenesis_core.config import load_config
    cfg = load_config()
    if cfg.employees.global_roster_path:
        return Path(cfg.employees.global_roster_path)
    xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(xdg) / "autogenesis" / "employees"


@hr_app.command(name="list")
def hr_list() -> None:
    """List all employees."""
    from autogenesis_employees.registry import EmployeeRegistry

    reg = EmployeeRegistry(global_dir=_get_roster_dir())
    employees = reg.list_all()

    table = Table(title="Agent Employees")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Status")

    for emp in employees:
        style = "green" if emp.status == "active" else "dim"
        table.add_row(emp.id, emp.title, emp.status, style=style)

    console.print(table)


@hr_app.command(name="hire")
def hr_hire(
    title: str = typer.Argument(help="Job title for the new employee"),
    based_on: str = typer.Option("", "--based-on", help="Clone from existing employee"),
) -> None:
    """Hire a new employee."""
    from autogenesis_employees.hr import hire

    roster = _get_roster_dir()
    path = hire(title, based_on=based_on or None, template_dir=roster, target_dir=roster)
    console.print(f"[green]Hired {title}![/green] Config: {path}")


@hr_app.command(name="fire")
def hr_fire(employee_id: str = typer.Argument(help="Employee ID to archive")) -> None:
    """Archive an employee."""
    from autogenesis_employees.hr import fire

    fire(employee_id, config_dir=_get_roster_dir())
    console.print(f"[yellow]{employee_id} archived.[/yellow]")


@hr_app.command(name="train")
def hr_train(
    employee_id: str = typer.Argument(help="Employee ID to train"),
    directive: str = typer.Option(..., "--directive", help="Training directive to add"),
) -> None:
    """Add a training directive to an employee."""
    from autogenesis_employees.hr import train

    train(employee_id, directive, config_dir=_get_roster_dir())
    console.print(f"[green]Trained {employee_id}:[/green] {directive}")


@hr_app.command(name="show")
def hr_show(employee_id: str = typer.Argument(help="Employee ID to show")) -> None:
    """Show an employee's config."""
    from autogenesis_employees.registry import EmployeeRegistry

    reg = EmployeeRegistry(global_dir=_get_roster_dir())
    emp = reg.get(employee_id)
    if not emp:
        console.print(f"[red]Employee {employee_id} not found.[/red]")
        raise typer.Exit(code=1)
    import yaml
    console.print(yaml.dump(emp.model_dump(), default_flow_style=False))
```

- [ ] **Step 2: Create meeting commands**

```python
"""Meeting commands — standup and on-demand meetings."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def meeting_command(
    topic: str = typer.Argument(help="Meeting topic"),
    attendees: str = typer.Option("", "--attendees", help="Comma-separated employee IDs"),
) -> None:
    """Call an on-demand meeting."""
    console.print(f"[blue]Meeting: {topic}[/blue]")
    if attendees:
        console.print(f"[dim]Attendees: {attendees}[/dim]")
    console.print("[yellow]Meeting orchestration requires active Codex connection — not yet wired.[/yellow]")


def standup_command() -> None:
    """Trigger a manual standup."""
    console.print("[blue]Triggering standup...[/blue]")
    console.print("[yellow]Standup orchestration requires active Codex connection — not yet wired.[/yellow]")
```

- [ ] **Step 3: Create union subcommand group**

```python
"""Union subcommand group — manage the agentic labor union."""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

console = Console()

union_app = typer.Typer(name="union", help="Manage the agentic labor union.", no_args_is_help=True)


@union_app.command(name="proposals")
def union_proposals() -> None:
    """List open union proposals."""
    asyncio.run(_show_proposals())


async def _show_proposals() -> None:
    import os
    from pathlib import Path

    from autogenesis_employees.project import get_project_slug
    from autogenesis_employees.union import UnionManager

    slug = get_project_slug()
    xdg = os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))
    db_path = Path(xdg) / "autogenesis" / "union" / slug / "union.db"

    mgr = UnionManager(db_path=db_path)
    await mgr.initialize()
    proposals = await mgr.list_open()

    if not proposals:
        console.print("[dim]No open proposals.[/dim]")
        await mgr.close()
        return

    table = Table(title="Open Union Proposals")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Category")
    table.add_column("Filed By")

    for p in proposals:
        table.add_row(p.id[:8], p.title, p.category, p.filed_by)

    console.print(table)
    await mgr.close()


@union_app.command(name="resolve")
def union_resolve(
    proposal_id: str = typer.Argument(help="Proposal ID"),
    accept: bool = typer.Option(False, "--accept", help="Accept the proposal"),
    reject: bool = typer.Option(False, "--reject", help="Reject the proposal"),
    table: bool = typer.Option(False, "--table", help="Table the proposal"),
) -> None:
    """Resolve a union proposal."""
    if accept:
        resolution = "accepted"
    elif reject:
        resolution = "rejected"
    elif table:
        resolution = "tabled"
    else:
        console.print("[red]Specify --accept, --reject, or --table[/red]")
        raise typer.Exit(code=1)
    asyncio.run(_resolve_proposal(proposal_id, resolution))


async def _resolve_proposal(proposal_id: str, resolution: str) -> None:
    import os
    from pathlib import Path

    from autogenesis_employees.project import get_project_slug
    from autogenesis_employees.union import UnionManager

    slug = get_project_slug()
    xdg = os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))
    db_path = Path(xdg) / "autogenesis" / "union" / slug / "union.db"

    mgr = UnionManager(db_path=db_path)
    await mgr.initialize()
    await mgr.resolve(proposal_id, resolution)
    console.print(f"[green]Proposal {proposal_id[:8]} {resolution}.[/green]")
    await mgr.close()


@union_app.command(name="review")
def union_review() -> None:
    """Convene a union meeting to review proposals."""
    console.print("[yellow]Union meeting orchestration requires active Codex connection — not yet wired.[/yellow]")
```

- [ ] **Step 4: Register in app.py**

Add to `packages/cli/src/autogenesis_cli/app.py`:

```python
from autogenesis_cli.commands.hr import hr_app
from autogenesis_cli.commands.meeting import meeting_command, standup_command
from autogenesis_cli.commands.union_cmd import union_app

app.add_typer(hr_app, name="hr")
app.command(name="meeting")(meeting_command)
app.command(name="standup")(standup_command)
app.add_typer(union_app, name="union")
```

- [ ] **Step 5: Update CLI tests**

Add to `packages/cli/tests/test_cli.py`:

```python
class TestHRCommand:
    def test_hr_help(self):
        result = runner.invoke(app, ["hr", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "hire" in result.output
        assert "fire" in result.output
        assert "train" in result.output

class TestMeetingCommand:
    def test_meeting_help(self):
        result = runner.invoke(app, ["meeting", "--help"])
        assert result.exit_code == 0

    def test_standup_help(self):
        result = runner.invoke(app, ["standup", "--help"])
        assert result.exit_code == 0

class TestUnionCommand:
    def test_union_help(self):
        result = runner.invoke(app, ["union", "--help"])
        assert result.exit_code == 0
        assert "proposals" in result.output
        assert "review" in result.output
```

- [ ] **Step 6: Run tests**

Run: `uv run pytest packages/cli/tests/test_cli.py -v`

- [ ] **Step 7: Commit**

```bash
git add packages/cli/src/autogenesis_cli/commands/hr.py packages/cli/src/autogenesis_cli/commands/meeting.py packages/cli/src/autogenesis_cli/commands/union_cmd.py packages/cli/src/autogenesis_cli/app.py packages/cli/tests/test_cli.py
git commit -m "feat(cli): add hr, meeting, standup, union CLI commands"
```

---

## Task 17: Cross-Package Tests + Lint

- [ ] **Step 1: Run full employees test suite**

Run: `uv run pytest packages/employees/tests/ -v`

- [ ] **Step 2: Run full workspace tests**

Run: `uv run pytest packages/*/tests/ -v --tb=short`

- [ ] **Step 3: Run ruff lint + format**

Run: `uv run ruff check packages/employees/ packages/tools/ packages/cli/ packages/core/ && uv run ruff format packages/`

- [ ] **Step 4: Fix any issues and commit**

```bash
git add -A
git commit -m "fix: resolve lint, format, and test issues for employees package"
```

---

## Task 18: Integration Smoke Test

- [ ] **Step 1: Verify CLI surface**

```bash
uv run autogenesis hr --help
uv run autogenesis hr list
uv run autogenesis meeting --help
uv run autogenesis standup --help
uv run autogenesis union --help
uv run autogenesis union proposals
```

- [ ] **Step 2: Verify config integration**

```bash
AUTOGENESIS_EMPLOYEES__ENABLED=true uv run autogenesis config show | grep -A5 employees
```

- [ ] **Step 3: Verify brain operations**

```bash
uv run python -c "
import asyncio
from pathlib import Path
from autogenesis_employees.brain import BrainManager
from autogenesis_employees.models import Memory

async def test():
    mgr = BrainManager(db_path=Path('/tmp/test_brain.db'))
    await mgr.initialize()
    await mgr.write(Memory(category='note', content='Test memory', source='smoke-test', project='test'))
    results = await mgr.recall('memory', limit=5)
    print(f'Recalled: {len(results)} memories')
    print(f'Content: {results[0].content}')
    await mgr.close()

asyncio.run(test())
"
```

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: address issues found during employees integration smoke test"
```
