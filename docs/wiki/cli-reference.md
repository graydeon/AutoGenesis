# CLI Reference

All commands: `uv run autogenesis <command>`

## Top-Level

| Command | Description |
|---------|-------------|
| `login` | OAuth PKCE login to OpenAI Codex |
| `logout` | Clear stored credentials |
| `run "prompt"` | Single-shot agent task |
| `chat` | Interactive chat session |
| `config show` | Print resolved config |
| `project init [PATH]` | Bootstrap `.autogenesis/config.yaml` + GitNexus index |

## Project (`project`)

| Command | Description |
|---------|-------------|
| `project init [PATH]` | Create/merge `.autogenesis/config.yaml` with GitNexus defaults and run `gitnexus analyze` |

### Examples

```bash
autogenesis project init .
autogenesis project init /path/to/repo --force-index
autogenesis project init . --skip-index
```

## CEO Orchestrator (`ceo`)

| Command | Description |
|---------|-------------|
| `ceo run "goal"` | Decompose goal → assign → dispatch → adapt |
| `ceo enqueue "task" [-p N]` | Push task to queue (priority N, higher=first) |
| `ceo dispatch [TASK_ID]` | Execute next queued task (or specific ID) |
| `ceo resume GOAL_ID` | Resume escalated goal from last incomplete subtask |
| `ceo status` | Table of all goals and tasks with status |
| `ceo plan GOAL_ID` | Print markdown plan for a goal |

### Examples

```bash
autogenesis ceo run "build user authentication with JWT"
autogenesis ceo enqueue "fix the CSS on the login page" --priority 5
autogenesis ceo dispatch                    # picks highest priority
autogenesis ceo status                      # see what's running
autogenesis ceo resume abc123def456         # resume after fixing escalation
```

## HR (`hr`)

| Command | Description |
|---------|-------------|
| `hr list` | List all employees (active + archived) |
| `hr hire "Title" [--based-on ID]` | Hire new employee (clone from template) |
| `hr fire EMPLOYEE_ID` | Archive an employee |
| `hr train EMPLOYEE_ID --directive "..."` | Add training directive |
| `hr show EMPLOYEE_ID` | Print employee YAML config |

### Examples

```bash
autogenesis hr hire "Data Engineer"
autogenesis hr hire "ML Engineer" --based-on backend-engineer
autogenesis hr train backend-engineer --directive "Always use type hints"
autogenesis hr fire intern
```

## Twitter (`twitter`)

| Command | Description |
|---------|-------------|
| `twitter start` | Start scheduler (foreground, Ctrl+C to stop) |
| `twitter stop` | Instructions for stopping |
| `twitter status` | Active window, queue counts, config |
| `twitter queue` | List pending tweet drafts |
| `twitter interview` | Persona interview (not yet wired) |

### Gateway (separate process)

```bash
python -m autogenesis_twitter.gateway --gateway-token <token>
# Listens on configurable host/port, loads Twitter API creds from env vars
```

## Meetings

| Command | Description |
|---------|-------------|
| `meeting "topic" [--attendees a,b,c]` | On-demand meeting (dispatches employees) |
| `standup` | Trigger manual standup for all active employees |

## Union (`union`)

| Command | Description |
|---------|-------------|
| `union proposals` | List open union proposals |
| `union resolve ID --accept/--reject/--table` | Resolve a proposal |
| `union review` | Convene union meeting (dispatches employees to vote) |
