# Agent Employee Architecture — Agentic Startup

**Goal:** Transform AutoGenesis's flat subagent model into a structured agentic startup where named employee agents have job titles, persistent memory, tools, inboxes, shared changelog, team meetings, and a labor union.

**Spec:** Approved via brainstorming session 2026-03-19.

---

## Architecture Overview

The orchestrator (main AutoGenesis agent loop) acts as the **CEO**. It reads the employee roster, autonomously decides who to assign tasks to based on role descriptions and expertise, and dispatches employees as subagents via `SubAgentManager`.

### Three Layers

**1. Employee Registry** — YAML config files defining each employee: job title, system prompt (persona + expertise), tool whitelist, environment config. Global roster at `~/.config/autogenesis/employees/`, project overrides at `.autogenesis/employees/`.

**2. Employee Runtime** — when the orchestrator dispatches an employee, it constructs a complete execution context: loads their config, injects their system prompt, restricts their tools, connects their brain.db, and delivers inbox messages. The employee runs as a Codex CLI subprocess.

**3. Shared Infrastructure** — brain.db (per-employee, per-project persistent memory), CHANGELOG.md (shared work log), inbox message queue (SQLite), meeting transcripts.

---

## Employee Registry

### Config File Format

Each employee is defined in a YAML file. Example `backend-engineer.yaml`:

```yaml
id: backend-engineer
title: Backend Engineer
persona: |
  You are a senior backend engineer at a tech startup. You write clean,
  well-tested Python code. You favor simplicity over cleverness. You
  always consider error handling and edge cases. You document your work
  in the changelog after completing tasks.
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

### Core Roster (9 employees)

| ID | Title | Specialization |
|---|---|---|
| `cto` | CTO / Lead Architect | Architecture decisions, system design, technical vision |
| `frontend-engineer` | Frontend Engineer | UI/UX, React, CSS, browser APIs, Pinchtab |
| `backend-engineer` | Backend Engineer | APIs, databases, Python, async, server-side logic |
| `devops-engineer` | DevOps / Infra Engineer | CI/CD, deployment, infra-dashboard, service management |
| `qa-engineer` | QA / Test Engineer | Testing strategy, test writing, coverage, validation |
| `security-engineer` | Security Engineer | Audits, vulnerability scanning, auth, crypto, guardrails |
| `technical-writer` | Technical Writer | Documentation, READMEs, API docs, changelogs |
| `product-manager` | Product Manager | Requirements, priorities, user stories, roadmap |
| `social-media-manager` | Social Media Manager | Twitter persona (wraps the TwitterAgent from packages/twitter/) |

Each gets a unique persona prompt, tool whitelist, and environment config. All share the infrastructure tools (brain, inbox, changelog, standup, union).

### Config Location

- **Global roster:** `~/.config/autogenesis/employees/{id}.yaml`
- **Project overrides:** `.autogenesis/employees/{id}.yaml` (merged on top of global)
- **Resolution:** project config deep-merges over global. A project can add `training_directives`, override `tools`, or change `status` without replacing the whole file.

### Hiring / Firing / Training

**Hire:** `autogenesis hr hire "Data Engineer" --based-on backend-engineer`
- Clones the base employee's config
- Generates a new ID (slugified title)
- User edits the persona/tools as needed
- Creates the YAML file in global or project scope (`--project` flag)

**Fire:** `autogenesis hr fire data-engineer`
- Sets `status: archived` in the config
- Does NOT delete the file or brain.db (preserves history)
- Archived employees are skipped by the orchestrator

**Train:** `autogenesis hr train backend-engineer --directive "Always use async/await patterns"`
- Appends to `training_directives` list in the YAML
- Training directives are injected into the system prompt after the base persona
- Can also hand-edit the YAML directly

**List:** `autogenesis hr list`
- Shows all employees with status, title, hired date

**Config files are the source of truth.** CLI commands are convenience wrappers that generate/modify YAML. You can always hand-edit.

---

## Brain (Persistent Memory)

Each employee gets their own `brain.db` — a per-employee, per-project SQLite database for long-term memory across sessions.

### What Goes in brain.db

- Decisions they've made and why
- Patterns they've learned about the codebase
- Things they've been told by other employees or by you
- Their own notes and observations
- Context from previous tasks on this project

### Schema

```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    project TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_accessed_at TEXT,
    relevance_score REAL DEFAULT 1.0
);
```

Categories: `decision`, `pattern`, `note`, `context`, `received`

### How It Works

- **On spin-up:** the orchestrator queries the employee's brain.db for top N memories by relevance score (default 20) and injects them into the system prompt as context
- **During work:** the employee uses `brain_write(category, content)` to store new memories and `brain_recall(query)` to search existing ones
- **Relevance decay:** memories that haven't been accessed lose relevance over time (0.95x multiplier per day). Accessed memories get boosted (reset to 1.0).
- **Pruning:** each brain.db capped at 1000 memories. When limit is reached, lowest-relevance memories are pruned automatically.

### Location

`$XDG_STATE_HOME/autogenesis/brains/{project-slug}/{employee-id}.db`

### Tools

- `brain_write(category: str, content: str)` — store a memory
- `brain_recall(query: str, limit: int = 5)` — search memories by keyword/semantic match

---

## Inbox & Messaging

Async inter-agent communication. Messages queue up and are delivered when an employee is spun up.

### How It Works

1. Employee A uses `send_message(to, subject, body)` during their session
2. Message goes into a shared SQLite message queue
3. Next time the recipient is spun up, the orchestrator reads their unread messages and injects them into the session context
4. Recipient can reply via `send_message`

### Message Schema

```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    from_employee TEXT NOT NULL,
    to_employee TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'unread',
    created_at TEXT NOT NULL,
    read_at TEXT
);
```

Status values: `unread`, `read`, `archived`

### Key Rules

- Messages are **never delivered mid-session** — only on spin-up. Prevents context pollution during focused work.
- The orchestrator includes unread messages in the employee's initial prompt: "INBOX: 2 unread messages" + contents
- Employees can send to `orchestrator` to escalate issues or request resources
- Messages to non-existent employees bounce with a logged warning
- Read messages are marked `read` with timestamp; employees can archive old messages

### Location

`$XDG_STATE_HOME/autogenesis/messages/{project-slug}/inbox.db`

One shared database per project.

---

## Changelog

All employees document their work in a shared `CHANGELOG.md` at the project root.

### How It Works

- Each employee has a `changelog_write` tool
- On task completion, they append a structured entry
- The tool handles formatting and timestamping
- Entries are append-only — employees never edit previous entries

### Entry Format

```markdown
## 2026-03-19 14:32 — Backend Engineer
**Task:** Implement user authentication endpoint
**Changes:** Added POST /api/auth/login with JWT token generation
**Files:** src/auth/routes.py, src/auth/jwt.py, tests/test_auth.py
**Notes:** Used bcrypt for password hashing. QA Engineer should review test coverage.
```

### Key Rules

- Plain markdown, human-readable, git-trackable
- Employees are instructed in their system prompt to always log their work
- On spin-up, the orchestrator injects the last N changelog entries (configurable, default 10) as context
- The orchestrator can also write entries (e.g., "Hired Data Engineer for this project")

### Location

`CHANGELOG.md` at project root (or configurable path)

---

## Meetings

Two types: scheduled standups (automatic) and on-demand discussions (triggered).

### Daily Standup

- Configurable schedule (default: once per day at start of active hours)
- The orchestrator spins up each active employee sequentially
- Each employee reads: their inbox, last 10 changelog entries, their brain memories
- Each posts a brief update via `standup_write` tool

**Standup format:**

```markdown
## Standup — 2026-03-19 09:00

### Backend Engineer
- **Yesterday:** Finished auth endpoint, JWT token generation
- **Today:** Starting database migration for user profiles
- **Blockers:** Need QA Engineer to review auth tests before I build on top of them

### QA Engineer
- **Yesterday:** Wrote integration test suite for API endpoints
- **Today:** Will review auth tests (Backend Engineer requested)
- **Blockers:** None
```

- Transcript saved to `$XDG_STATE_HOME/autogenesis/meetings/{project-slug}/standup-YYYY-MM-DD.md`
- If an employee mentions a blocker involving another employee, the orchestrator auto-generates an inbox message to that employee

### On-Demand Meetings

- Triggered via: `autogenesis meeting "Topic" --attendees backend-engineer,qa-engineer,security-engineer`
- Or the orchestrator calls one when it detects a cross-cutting concern
- Round-table format: each attendee spun up in sequence, reads what others said, responds
- 2-3 rounds max to keep costs bounded
- Transcript saved to `meetings/{project-slug}/meeting-YYYY-MM-DD-HHMMSS.md`

### Meeting Config

```yaml
meetings:
  standup_enabled: true
  standup_time: "09:00"
  standup_timezone: "America/New_York"
  max_meeting_rounds: 3
```

---

## Labor Union

Employees have a collective voice on company direction through the agentic labor union.

### How It Works

- Any employee can file a "union proposal" via the `union_propose` tool
- Proposals accumulate in a union ledger (SQLite)
- Periodically (weekly, or on-demand via `autogenesis union review`), the orchestrator convenes a union meeting
- All employees are spun up, presented with proposals, and each votes/comments
- The meeting produces a recommendation document surfaced to the user
- The user accepts, rejects, or tables each recommendation

### Proposal Categories

- `hiring` — "We need a new role"
- `tooling` — "We need access to tool X"
- `process` — "Standups should include code review status"
- `architecture` — "We should refactor module Y"
- `workload` — "Backend Engineer is overloaded, need to redistribute"

### Proposal Schema

```sql
CREATE TABLE proposals (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    rationale TEXT NOT NULL,
    category TEXT NOT NULL,
    filed_by TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    resolution TEXT
);

CREATE TABLE votes (
    id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL REFERENCES proposals(id),
    employee_id TEXT NOT NULL,
    vote TEXT NOT NULL,
    comment TEXT,
    created_at TEXT NOT NULL
);
```

Vote values: `support`, `neutral`, `oppose`
Status values: `open`, `accepted`, `rejected`, `tabled`

### Union Meeting Output

```markdown
## Union Meeting — 2026-03-19

### Proposal: Hire a Data Engineer
- Filed by: Backend Engineer
- Votes: 5 support, 1 neutral, 0 oppose
- Discussion: QA Engineer agrees — test data generation is painful without SQL expertise
- **Recommendation:** HIRE

### Proposal: Add Docker tool access for DevOps
- Filed by: DevOps Engineer
- Votes: 3 support, 3 neutral, 0 oppose
- **Recommendation:** APPROVE
```

### Location

- Ledger: `$XDG_STATE_HOME/autogenesis/union/{project-slug}/union.db`
- Meeting transcripts: `$XDG_STATE_HOME/autogenesis/union/{project-slug}/meeting-YYYY-MM-DD.md`

---

## Orchestrator Integration

### Task Assignment

When a task arrives, the orchestrator:
1. Reads the employee roster (active employees only)
2. Considers the task description, each employee's title/persona/expertise
3. Autonomously selects the best employee(s) for the task
4. Constructs the employee's execution context (system prompt + brain memories + inbox + recent changelog)
5. Dispatches via `SubAgentManager`
6. Collects results

For multi-disciplinary tasks, the orchestrator can dispatch sequentially (Backend Engineer implements, then QA Engineer reviews) or note in the changelog that multiple employees contributed.

### Employee Spin-Up Context Injection

When an employee session starts, the orchestrator builds their prompt:

```
[Employee persona from YAML]
[Training directives]
[Top 20 brain memories by relevance]
[Last 10 changelog entries]
[Unread inbox messages]
[Current task assignment]
```

This gives the employee full context without them needing to read files or query databases themselves.

### Infrastructure Tools (Available to All Employees)

| Tool | Purpose |
|---|---|
| `brain_write` | Store a memory in their brain.db |
| `brain_recall` | Search their memories |
| `send_message` | Send async message to another employee |
| `changelog_write` | Document completed work |
| `standup_write` | Post standup update |
| `union_propose` | File a union proposal |

These are in addition to each employee's role-specific tools.

---

## SubAgentManager Integration Contract

### How Employee Context Reaches the Subprocess

`SubAgentManager.spawn()` is extended with two new optional parameters:

```python
async def spawn(
    self,
    task: str,
    cwd: str,
    timeout: float = 300.0,
    system_prompt: str | None = None,  # NEW
    env_overrides: dict[str, str] | None = None,  # NEW
) -> SubAgentResult:
```

The `system_prompt` is written to a temporary file and passed to Codex CLI via the `--system-prompt-file` flag. The `env_overrides` are merged into the subprocess environment alongside the existing `AUTOGENESIS_AGENT_DEPTH`.

`EmployeeRuntime.dispatch()` does:
1. Loads the employee config from the registry
2. Builds the full system prompt (persona + training + brain memories + inbox + changelog + task)
3. Writes it to a temp file in `$XDG_RUNTIME_DIR/autogenesis/`
4. Calls `SubAgentManager.spawn(task, cwd, system_prompt=temp_file_path, env_overrides=employee.env)`
5. Cleans up the temp file after the subprocess exits

### Tool Whitelist Enforcement

Tool restriction happens via the system prompt, not a runtime enforcement mechanism. The employee's system prompt includes:

```
You have access to ONLY these tools: bash, file_read, file_write, ...
Do not attempt to use tools not in this list.
```

This is the same approach Claude Code and Codex CLI use — tool availability is declared in the prompt, and the model respects it. The actual tool definitions passed to the Codex CLI `--tools` flag are filtered to only include the employee's allowed tools.

`EmployeeRuntime` filters tools by intersecting the employee's `tools` list with the registered tools in `ToolRegistry`, and passes only those definitions to the Codex CLI invocation.

### Error Handling for Failed Sessions

When `SubAgentManager.spawn()` returns a non-success result:
- **Timeout:** log `employee.session.timeout` event, record in changelog ("Backend Engineer session timed out on task X"), notify orchestrator
- **Exit code != 0:** log `employee.session.failed` event, include stderr/stdout in the log. Orchestrator decides whether to retry (same employee), reassign (different employee), or escalate to the user.
- **Retry policy:** max 1 automatic retry per employee per task. After that, the orchestrator logs the failure and continues with other work.

### Recursive Sub-Agent Delegation

Employees with `sub_agent` in their tool list can spawn sub-agents. These are **generic sub-agents**, not other employees. The existing `AUTOGENESIS_AGENT_DEPTH` counter prevents infinite recursion. If an employee needs another employee's help, they use `send_message` (async inbox), not `sub_agent`.

---

## Employee Lifecycle Events

New event types added to `EventType`:

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

---

## Project Slug Derivation

The `{project-slug}` used in brain.db, inbox, and union paths is derived from the project's working directory:

1. If `.autogenesis/config.yaml` exists and contains a `project_name` field, use that (slugified)
2. Otherwise, use the basename of the git repository root (via `git rev-parse --show-toplevel`)
3. If not in a git repo, use the basename of the current working directory
4. Slugification: lowercase, replace non-alphanumeric with hyphens, strip leading/trailing hyphens

Example: `/home/gray/dev/AutoGenesis` → `autogenesis`

This is computed once per orchestrator session and passed to all managers.

---

## Standup Scheduling

Daily standups are triggered by the orchestrator's main loop, not a separate scheduler process:

- When the orchestrator starts (or on each cycle if running continuously), it checks if a standup is due: `is_standup_due(last_standup_date, standup_time, timezone)`
- If the current time is past `standup_time` and no standup has run today, the orchestrator runs the standup before processing any tasks
- The `autogenesis standup` CLI command triggers a manual standup regardless of schedule
- Standup completion is recorded in a lightweight state file at `$XDG_STATE_HOME/autogenesis/standup_last_run.txt`

---

## Brain Recall Implementation

`brain_recall(query)` uses **SQLite FTS5** (full-text search) — no embeddings, no vector store, no new dependencies.

```sql
CREATE VIRTUAL TABLE memories_fts USING fts5(content, source, category);
```

On `brain_write`, a row is inserted into both `memories` and `memories_fts`. On `brain_recall(query)`, the FTS5 index is searched:

```sql
SELECT m.* FROM memories m
JOIN memories_fts fts ON m.id = fts.rowid
WHERE memories_fts MATCH ?
ORDER BY m.relevance_score DESC
LIMIT ?
```

This provides keyword-based search that's fast, requires no external dependencies, and is good enough for finding relevant memories by topic. Semantic search can be layered on later if needed.

---

## CLI Commands

### HR Commands

```
autogenesis hr list                                    # List all employees
autogenesis hr hire "Data Engineer" --based-on backend-engineer  # Hire new employee
autogenesis hr fire data-engineer                      # Archive an employee
autogenesis hr train backend-engineer --directive "..."  # Add training directive
autogenesis hr show backend-engineer                   # Show employee config
```

### Meeting Commands

```
autogenesis meeting "Topic" --attendees id1,id2,id3    # On-demand meeting
autogenesis standup                                    # Trigger manual standup
```

### Union Commands

```
autogenesis union review                               # Convene union meeting
autogenesis union proposals                            # List open proposals
autogenesis union resolve <id> --accept|--reject|--table  # Resolve a proposal
```

---

## Package Structure

### New Package: `packages/employees/`

```
packages/employees/
  pyproject.toml
  src/autogenesis_employees/
    __init__.py
    registry.py         # EmployeeRegistry — load, merge, resolve employee configs
    runtime.py          # EmployeeRuntime — build execution context, dispatch
    brain.py            # BrainManager — per-employee SQLite memory CRUD
    inbox.py            # InboxManager — message queue CRUD
    changelog.py        # ChangelogManager — append-only markdown writer
    meetings.py         # MeetingManager — standup + on-demand orchestration
    union.py            # UnionManager — proposal ledger, voting, meeting output
    models.py           # EmployeeConfig, Memory, Message, Proposal, Vote, StandupEntry
    hr.py               # Hire/fire/train operations on YAML configs
  templates/
    cto.yaml
    frontend-engineer.yaml
    backend-engineer.yaml
    devops-engineer.yaml
    qa-engineer.yaml
    security-engineer.yaml
    technical-writer.yaml
    product-manager.yaml
    social-media-manager.yaml
  tests/
    test_registry.py
    test_runtime.py
    test_brain.py
    test_inbox.py
    test_changelog.py
    test_meetings.py
    test_union.py
    test_models.py
    test_hr.py
```

### New Tools in `packages/tools/`

```
brain.py             # brain_write + brain_recall tools
messaging.py         # send_message tool
changelog_tool.py    # changelog_write tool
standup.py           # standup_write tool
union_tool.py        # union_propose tool
```

### CLI Commands in `packages/cli/`

```
commands/hr.py       # autogenesis hr subcommand group
commands/meeting.py  # autogenesis meeting + standup commands
commands/union.py    # autogenesis union subcommand group
```

### Config Addition

```python
class EmployeesConfig(BaseModel):
    """Agent employee configuration."""

    enabled: bool = False
    global_roster_path: str = ""  # empty = XDG_CONFIG_HOME/autogenesis/employees/ (resolved at runtime via _xdg_config_home())
    standup_enabled: bool = True
    standup_time: str = "09:00"
    standup_timezone: str = "America/New_York"
    max_meeting_rounds: int = 3
    brain_memory_limit: int = 1000
    brain_context_limit: int = 20
    changelog_context_limit: int = 10

class AutoGenesisConfig(BaseModel):
    # ... existing fields ...
    employees: EmployeesConfig = Field(default_factory=EmployeesConfig)
```

### Dependencies

`packages/employees/pyproject.toml` dependencies:
- `autogenesis-core` — config, events, models, SubAgentManager
- `autogenesis-tools` — Tool base class for infrastructure tools
- `aiosqlite>=0.20` — already in workspace (brain.db, inbox.db, union.db)
- `pyyaml>=6.0` — already in workspace (employee YAML configs)
- `structlog>=24.0` — already in workspace
- `pydantic>=2.0` — already in workspace
- No new heavy dependencies

### Meeting Cost Controls

On-demand meetings default to max 3 attendees unless explicitly overridden. With `max_meeting_rounds: 3`, that's 9 Codex CLI invocations max per meeting. Standups spin up each employee once (9 invocations for full roster). The orchestrator can be selective — only spin up employees who have had recent activity (checked via changelog entries in the last 24h) to reduce standup cost.
