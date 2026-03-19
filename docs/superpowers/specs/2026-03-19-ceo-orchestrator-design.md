# CEO Orchestrator Design Spec

## Overview

The CEO Orchestrator is the central brain of the AutoGenesis agent employee system. It accepts high-level goals or explicit tasks, decomposes them into subtasks, assigns them to employees using LLM reasoning, dispatches them via SubAgentManager, and adapts the plan based on results.

## Design Decisions

- **Task queue + goal decomposition** — Two entry points: explicit task queue for directed work, and goal-driven decomposition for high-level objectives.
- **LLM-driven employee assignment** — Codex reasons about the roster (titles, personas, tools, training) to pick the best employee for each subtask.
- **Rolling dispatch with re-evaluation** — After each subtask completes, the CEO re-evaluates the remaining plan in light of results before dispatching the next.
- **Retry once on failure, then escalate** — Failed dispatches get one retry with failure context injected. Second failure escalates to the user.
- **SQLite for operational state, markdown for plans** — Structured data in `ceo.db`, human-readable plans as markdown files.

## Architecture

### Core Class: `CEOOrchestrator`

Location: `packages/employees/src/autogenesis_employees/orchestrator.py`

Holds references to:
- `CEOStateManager` — SQLite CRUD for `ceo.db`
- `EmployeeRegistry` — loads active employees from YAML configs
- `EmployeeRuntime` — builds system prompts with brain/inbox/changelog context
- `SubAgentManager` — spawns Codex CLI subprocesses
- `CodexClient` — for the CEO's own reasoning calls (decompose, assign, re-evaluate)
- Per-employee manager cache (`dict[str, ManagerBundle]`) — lazily initialized `BrainManager`, `InboxManager`, `ChangelogManager` per employee

### Data Models

```python
@dataclass
class ManagerBundle:
    brain: BrainManager
    inbox: InboxManager

class SubtaskResult(BaseModel):
    subtask: str
    employee_id: str
    status: str  # completed / failed / escalated
    output: str
    attempt: int
    duration_seconds: float

class GoalResult(BaseModel):
    goal_id: str
    status: str  # completed / escalated
    subtask_results: list[SubtaskResult]
    plan_path: str

class TaskResult(BaseModel):
    task_id: str
    status: str  # completed / failed / escalated
    employee_id: str | None = None
    output: str = ""
    duration_seconds: float = 0.0

class GoalStatus(BaseModel):
    goal_id: str
    description: str
    status: str
    subtasks_completed: int
    subtasks_total: int
    plan_path: str

class TaskStatus(BaseModel):
    task_id: str
    description: str
    status: str
    priority: int
```

### Entry Points

1. **`async enqueue(description: str, priority: int = 0) -> str`** — Push a task onto the queue. Returns task ID. No execution.
2. **`async run(goal: str) -> GoalResult`** — Decompose a high-level goal into subtasks, then execute via rolling dispatch.
3. **`async dispatch(task_id: str | None = None) -> TaskResult`** — Execute next queued task (or a specific one by ID).
4. **`async status() -> list[GoalStatus | TaskStatus]`** — Return current state of all goals and tasks.
5. **`async resume(goal_id: str) -> GoalResult`** — Resume an in-progress or escalated goal from last incomplete subtask.
6. **`async close() -> None`** — Close all lazily-opened manager connections (BrainManager, InboxManager) and the state DB.

### Pre-checks

Before any dispatch (run or standalone), the orchestrator validates:
- `EmployeeRegistry.list_active()` returns at least one employee. If empty, raises immediately with a clear error ("No active employees — use `autogenesis hr hire` to add employees").

### Working Directory Resolution

All employee dispatches use the **project root** as `cwd` — the directory containing `.autogenesis/`. Resolved once at orchestrator init via upward directory walk from `os.getcwd()`. Falls back to `os.getcwd()` if no `.autogenesis/` directory is found.

### Dispatch Timeout

Employee dispatch timeout defaults to `300.0` seconds (SubAgentManager default). Configurable via `EmployeesConfig.dispatch_timeout: float = 300.0`. The decompose call may also suggest per-subtask timeouts; if provided, they override the default.

### Run Loop

Execution is **sequential** — one subtask at a time, no parallel dispatch. This keeps the re-evaluation step meaningful and avoids conflicts.

```
run(goal) →
  1. Pre-check: verify active employees exist
  2. Decompose: Codex call breaks goal into ordered subtasks → save as markdown plan
  3. Store goal record in SQLite (status: executing)
  4. Pick next incomplete subtask from plan
  5. Assign: Codex call with roster + subtask → picks employee_id
  6. Build context:
     a. Get managers: brain = _get_managers(employee_id).brain, inbox = ...
     b. brain_context = [m.content for m in await brain.top_memories(config.brain_context_limit)]
     c. inbox_messages = [f"From {m.from_employee}: {m.subject}\n{m.body}" for m in await inbox.get_unread(employee_id)]
     d. changelog_entries = changelog.read_recent(config.changelog_context_limit)
     e. system_prompt = EmployeeRuntime.build_system_prompt(employee_config, brain_context, inbox_messages, changelog_entries, subtask)
  7. Dispatch: SubAgentManager.spawn(subtask, cwd=project_root, timeout=dispatch_timeout, system_prompt=system_prompt, env_overrides=employee_config.env)
  8. Record execution in SQLite
  9. On success:
     - Store result, mark subtask complete in plan markdown
     - Employee writes to changelog via ChangelogWriteTool (part of their system prompt instructions)
     - Re-evaluate: Codex call with plan + results → may revise remaining subtasks
  10. On failure:
     - Attempt 1: Retry with failure output injected into system prompt
     - Attempt 2: Mark as escalated, pause goal, surface to user
  11. Repeat 4-10 until plan complete or escalation
```

### Dispatch (standalone task)

```
dispatch(task_id) →
  1. Pull task from SQLite queue (highest priority pending, or specific ID)
  2. Assign employee via Codex reasoning call
  3. Build context, dispatch, collect result (same as run loop steps 5-7)
  4. On success: mark task completed
  5. On failure: retry once, then mark escalated
```

## State Management

### SQLite: `ceo.db`

Location: `.autogenesis/ceo/ceo.db`

#### `tasks` table — explicit task queue

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | uuid hex |
| description | TEXT | task description |
| status | TEXT | pending / in_progress / completed / failed / escalated |
| priority | INTEGER | higher = dispatched first, default 0 |
| created_at | TEXT | ISO datetime |
| completed_at | TEXT | nullable |
| result | TEXT | nullable, employee output summary |

#### `goals` table — goal decomposition tracking

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | uuid hex |
| description | TEXT | original goal text |
| plan_path | TEXT | path to markdown plan file |
| status | TEXT | planning / executing / completed / failed / escalated |
| created_at | TEXT | ISO datetime |
| completed_at | TEXT | nullable |

#### `executions` table — dispatch log

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | uuid hex |
| goal_id | TEXT | nullable FK to goals |
| task_id | TEXT | nullable FK to tasks |
| subtask | TEXT | what was dispatched |
| employee_id | TEXT | who did it |
| attempt | INTEGER | 1 or 2 |
| status | TEXT | running / completed / failed / timed_out |
| output | TEXT | employee output |
| started_at | TEXT | ISO datetime |
| finished_at | TEXT | nullable |

Constraint: `CHECK (goal_id IS NOT NULL OR task_id IS NOT NULL)` — every execution belongs to either a goal or a standalone task.

### Markdown Plans

Location: `.autogenesis/ceo/plans/goal-{id}.md`

Format:
```markdown
# Goal: {description}

Created: {datetime}
Status: {executing/completed/escalated}

## Subtasks

- [x] **1. {subtask description}**
  Assigned to: {employee_id}
  Result: {summary}

- [ ] **2. {subtask description}**
  (pending)

- [ ] **3. {subtask description}**
  (pending)
```

Updated in-place as subtasks complete. After re-evaluation, subtasks may be added, removed, or reordered — the markdown reflects the current plan state.

## LLM Reasoning Calls

The CEO makes three types of internal Codex calls via `CodexClient.create_response_sync()` (async method returning `CompletionResult`). JSON is extracted from `result.text`:

### 1. Decompose Call

- **Input:** goal description, employee roster summary (id, title, persona, tools), recent changelog entries
- **System prompt:** "You are the CEO of a software startup. Decompose this goal into concrete, ordered subtasks. Each subtask should be completable by one employee in one session. Consider the available team and their capabilities."
- **Expected output:** JSON array of `{"description": str, "rationale": str}`
- **Parsing:** Extract JSON block from response via regex, `json.loads()`

### 2. Assign Call

- **Input:** subtask description, overall goal context, full roster details (id, title, persona, tools, training_directives), previous subtask results (if any)
- **System prompt:** "Given this subtask and your available employees, pick the single best employee to handle it. Consider their tools, training, and expertise."
- **Expected output:** JSON `{"employee_id": str, "reasoning": str}`
- **Parsing:** Same JSON extraction pattern

### 3. Re-evaluate Call

- **Input:** original goal, full plan with completed/remaining subtasks, latest result
- **System prompt:** "Review the implementation plan in light of the latest completed work. Should remaining subtasks be changed, added, removed, or reordered? If no changes needed, say so."
- **Expected output:** JSON `{"no_changes": true}` or JSON array of updated remaining subtasks
- **Parsing:** Same JSON extraction pattern

### JSON Extraction

All reasoning calls use the same extraction utility:

```python
def extract_json(text: str) -> Any:
    """Extract first JSON array or object from text."""
    # Try ```json fenced blocks first, then raw JSON detection
```

## Error Handling

### Employee Dispatch Failure

1. Non-zero exit code or timeout from SubAgentManager.spawn()
2. First attempt: re-dispatch same employee with failure output in system prompt as "Previous attempt failed with: {output}. Analyze what went wrong and try a different approach."
3. Second attempt failure:
   - Mark execution as "failed" in SQLite
   - Mark subtask as "escalated" in plan markdown
   - If part of a goal: set goal status to "escalated", pause execution
   - Print full context to terminal for user review
4. User can fix manually and `ceo resume <goal_id>` to continue

### CEO Reasoning Failure

If a decompose/assign/re-evaluate call fails to produce parseable JSON:
- Retry the call once with a more explicit "respond ONLY with valid JSON" instruction
- If still unparseable: escalate to user with raw output

## Per-Employee Manager Lifecycle

Managers are initialized lazily per employee on first assignment:

```python
# ManagerBundle is a @dataclass (defined in Data Models section above)

# In CEOOrchestrator:
_managers: dict[str, ManagerBundle] = {}

async def _get_managers(self, employee_id: str) -> ManagerBundle:
    if employee_id not in self._managers:
        data_dir = self._base_dir / "employees" / employee_id
        brain = BrainManager(data_dir / "brain.db")
        inbox = InboxManager(data_dir / "inbox.db")
        await brain.initialize()
        await inbox.initialize()
        self._managers[employee_id] = ManagerBundle(brain=brain, inbox=inbox)
    return self._managers[employee_id]

async def close(self) -> None:
    for bundle in self._managers.values():
        await bundle.brain.close()
        await bundle.inbox.close()
    self._managers.clear()
    await self._state.close()
```

`ChangelogManager` is shared (one changelog for the whole team), not per-employee. Initialized once in `CEOOrchestrator.__init__()` with path `.autogenesis/changelog.md`.

## CLI Integration

New file: `packages/cli/src/autogenesis_cli/commands/ceo.py`

Registered in `app.py` as: `app.add_typer(ceo_app, name="ceo")`

### Commands

| Command | Description |
|---------|-------------|
| `autogenesis ceo enqueue "description" [--priority N]` | Push task to queue |
| `autogenesis ceo run "goal description"` | Decompose and execute goal |
| `autogenesis ceo dispatch [TASK_ID]` | Execute next queued task or specific one |
| `autogenesis ceo status` | Rich table of goals and tasks |
| `autogenesis ceo plan GOAL_ID` | Print markdown plan |
| `autogenesis ceo resume GOAL_ID` | Resume escalated/paused goal |

### Output

- During execution: Rich live display showing current subtask, assigned employee, and streaming status
- On completion: summary table of all subtasks with employee, status, and duration
- On escalation: full failure context with employee output

## File Layout

### New Files

```
packages/employees/src/autogenesis_employees/
  orchestrator.py    — CEOOrchestrator class
  state.py           — CEOStateManager (SQLite CRUD for ceo.db)

packages/cli/src/autogenesis_cli/commands/
  ceo.py             — Typer sub-app for CEO commands
```

### Modified Files

```
packages/cli/src/autogenesis_cli/app.py
  — Register ceo_app sub-typer

packages/core/src/autogenesis_core/events.py
  — Add CEO event types following existing dot-notation convention:
    CEO_GOAL_START = "ceo.goal.start"
    CEO_SUBTASK_ASSIGN = "ceo.subtask.assign"
    CEO_SUBTASK_COMPLETE = "ceo.subtask.complete"
    CEO_SUBTASK_FAIL = "ceo.subtask.fail"
    CEO_ESCALATION = "ceo.escalation"
    CEO_GOAL_COMPLETE = "ceo.goal.complete"

packages/core/src/autogenesis_core/config.py
  — Add dispatch_timeout: float = 300.0 to EmployeesConfig
```

### Data Directory

```
.autogenesis/
  changelog.md              — shared team changelog
  ceo/
    ceo.db                  — task queue, goals, executions
    plans/
      goal-{id}.md          — decomposed plans
  employees/
    {employee_id}/
      brain.db              — per-employee persistent memory
      inbox.db              — per-employee message queue
```

## Testing Strategy

- Unit tests for `CEOStateManager` (SQLite CRUD operations)
- Unit tests for JSON extraction utility
- Unit tests for `CEOOrchestrator` with mocked `CodexClient` and `SubAgentManager` — verify the run loop logic, retry behavior, and re-evaluation flow
- Integration test: mock Codex responses to simulate full goal → decompose → assign → dispatch → complete cycle
