# CEO Orchestrator

## What It Does

Central brain that turns high-level goals into completed work by:
1. Decomposing goals into subtasks (via Codex LLM call)
2. Assigning each subtask to the best employee (via Codex LLM call)
3. Dispatching employees sequentially via SubAgentManager
4. Re-evaluating the plan after each completion
5. Retrying once on failure, then escalating to user

## Two Entry Points

### Goal Decomposition (`ceo run`)
```
"Build user auth" → [schema design, backend API, tests, frontend] → assign → dispatch → adapt
```

### Task Queue (`ceo enqueue` + `ceo dispatch`)
```
"Fix login bug" → queue (priority) → assign → dispatch
```

## Run Loop

```
run(goal) →
  1. Decompose via Codex → ordered subtask list
  2. Create goal record in ceo.db + write plan markdown
  3. For each subtask:
     a. Assign via Codex (considers roster, tools, training, previous results)
     b. Build employee context (brain + inbox + changelog + task)
     c. Dispatch via SubAgentManager.spawn()
     d. On success: record, update plan, re-evaluate remaining
     e. On failure: retry once with failure context injected
     f. On second failure: escalate, pause goal
  4. Return GoalResult (completed or escalated)
```

## State Storage

| Store | Location | Purpose |
|-------|----------|---------|
| `ceo.db` | `.autogenesis/ceo/ceo.db` | Task queue, goal records, execution log |
| Plan files | `.autogenesis/ceo/plans/goal-{id}.md` | Human-readable subtask tracking |

### ceo.db Tables

**tasks**: id, description, status (pending/in_progress/completed/failed/escalated), priority, created_at, completed_at, result

**goals**: id, description, plan_path, status (planning/executing/completed/failed/escalated), created_at, completed_at

**executions**: id, goal_id, task_id, subtask, employee_id, attempt (1 or 2), status (running/completed/failed/timed_out), output, started_at, finished_at

## LLM Reasoning Calls

The CEO makes 3 types of Codex calls (all return JSON):

| Call | Input | Output |
|------|-------|--------|
| **Decompose** | goal + roster + changelog | `[{"description": "...", "rationale": "..."}]` |
| **Assign** | subtask + goal context + roster + previous results | `{"employee_id": "...", "reasoning": "..."}` |
| **Re-evaluate** | goal + plan + latest result | `{"no_changes": true}` or updated subtask array |

JSON extracted from response via regex (fenced blocks first, then raw scan). Retries once with stricter prompt on parse failure.

## Resume After Escalation

```bash
autogenesis ceo resume <goal_id>
```

Parses remaining unchecked subtasks from plan markdown, re-enters dispatch loop with existing goal_id. Previous results loaded from executions table.

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Employee dispatch fails (exit code != 0) | Retry once with failure output in prompt |
| Second failure | Mark escalated, pause goal, surface to user |
| No active employees | Raise immediately: "No active employees — use `autogenesis hr hire`" |
| JSON parse failure from Codex | Retry once with stricter "respond ONLY with JSON" prompt |
| No pending tasks in queue | Raise: "No pending tasks in queue" |

## Config

```yaml
employees:
  dispatch_timeout: 300.0   # seconds per employee dispatch (default 5 min)
```
