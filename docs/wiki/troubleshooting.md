# Troubleshooting

**Last updated:** 2026-04-24

## Decision Tree

```
Problem?
├── Import errors → §1
├── Tests failing → §2
├── CEO dispatch issues → §3
├── Twitter issues → §4
├── Employee issues → §5
├── Config not loading → §6
├── Auth/credential issues → §7
└── Database issues → §8
```

---

## §1: Import Errors

**`ModuleNotFoundError: No module named 'autogenesis_*'`**

Cause: Package not installed in current Python environment.

```bash
# Install all workspace packages in dev mode
uv sync --all-packages

# Or install specific package
uv pip install -e packages/core
uv pip install -e packages/employees
```

**Pyright reports `reportMissingImports` for all workspace packages**

This is a **known false positive**. Pyright cannot resolve uv workspace editable installs. Ignore these. Tests are the source of truth — run `uv run python -m pytest` to verify.

---

## §2: Tests Failing

**Run tests correctly:**
```bash
uv run pytest packages/*/tests tests -q --tb=short
```

Do NOT use bare `python -m pytest` — must use `uv run` to get workspace packages on path.

**Coverage gate used by CI**

```bash
uv run pytest packages/*/tests/ -q --tb=short --cov --cov-report=term-missing --cov-fail-under=80
```

**Ruff or mypy fails even though tests pass**

As of 2026-04-24, full Ruff lint and strict mypy pass locally. If either fails, first run `uv sync --all-extras`, then check [Status Report](status-report.md) for the current expected baseline.

**Pre-commit hook fails with ruff errors**

```bash
uv run ruff check packages/ --fix    # auto-fix what's safe
uv run ruff format packages/         # format
```

Common ruff issues:
- `TC001/TC003`: Move import to TYPE_CHECKING block
- `PLR2004`: Magic number → extract constant or add `# noqa: PLR2004`
- `PLC0415`: Import inside function → add `# noqa: PLC0415` (intentional lazy import)
- `S608`: SQL injection false positive on dynamic UPDATE SET → add `# noqa: S608`
- `PERF401`: Use `list.extend(generator)` instead of loop append

---

## §3: CEO Dispatch Issues

**"No active employees"**

```bash
autogenesis hr list              # check roster
autogenesis hr hire "Backend Engineer"   # hire if empty
```

Employee YAML must exist in global roster dir: `$XDG_CONFIG_HOME/autogenesis/employees/`

**Goal stuck in "escalated" status**

Employee failed twice. Check execution output:
```bash
autogenesis ceo plan <goal_id>   # see which subtask failed
```

Fix the underlying issue, then:
```bash
autogenesis ceo resume <goal_id>  # picks up from last incomplete subtask
```

**"Decompose returned empty or invalid subtasks"**

Codex LLM call returned non-JSON or empty array. Causes:
- No Codex credentials configured (auth.json missing)
- API rate limit or server error
- Goal too vague for decomposition

**Dispatch timeout (default 300s)**

Increase in config:
```yaml
employees:
  dispatch_timeout: 600.0
```

**"No pending tasks in queue"**

Queue is empty. Enqueue something first:
```bash
autogenesis ceo enqueue "task description"
```

---

## §4: Twitter Issues

**Gateway not running**

```bash
# Check if gateway is listening
curl http://127.0.0.1:1456/health
# Expected: {"status": "ok"}

# Start gateway
python -m autogenesis_twitter.gateway --gateway-token <token>
```

Gateway needs Twitter API credentials. Set these environment variables: `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET`, `TWITTER_BEARER_TOKEN`

**Scheduler exits immediately**

- Check `twitter.enabled` is `true` in config
- Check current time is within `active_hours_start` - `active_hours_end` (in configured timezone)
- Check `twitter status` to see active window

**Tweets not posting**

```
Queue has approved items? → autogenesis twitter queue
Gateway running?          → curl $GATEWAY_URL/health
Gateway token matches?    → AUTOGENESIS_GATEWAY_TOKEN env var
Twitter API creds valid?  → Check TWITTER_* env vars are set
```

Current audit note: [Security Audit](security-audit.md) found that the poster expects a different success field than the gateway returns and calls a status route the gateway does not implement. Fix that contract before treating posting failures as credential-only problems.

**Queue panel not showing in your dashboard**

Check `AUTOGENESIS_TWITTER_QUEUE_DB` env var points to the correct SQLite file. Default: `$XDG_STATE_HOME/autogenesis/twitter_queue.db`

---

## §5: Employee Issues

**Employee not being assigned work**

- Check `status: active` in YAML (not "archived")
- Check employee is in global roster dir or project override dir
- Run `autogenesis hr show <id>` to verify config loads

**Brain memory not persisting**

Brain DB lives at `.autogenesis/employees/{id}/brain.db`. Check:
- Directory exists and is writable
- Employee was dispatched at least once (lazy init)

**Messages not delivered**

Inbox DB at `.autogenesis/employees/{id}/inbox.db`. Messages are injected into system prompt on next dispatch — they don't trigger real-time notifications.

---

## §6: Config Not Loading

**Debug: print resolved config**
```bash
autogenesis config show
```

**Environment variable not taking effect**

Pattern: `AUTOGENESIS_` + uppercase + `__` for nesting.
```bash
# Wrong:
AUTOGENESIS_EMPLOYEES_ENABLED=true

# Right:
AUTOGENESIS_EMPLOYEES__ENABLED=true    # double underscore
```

**Project config not found**

Walks up from cwd looking for `.autogenesis/config.yaml`. Make sure you're inside the project directory (or a subdirectory).

---

## §7: Auth/Credential Issues

**"AuthenticationError" from Codex**

```bash
autogenesis login    # re-authenticate via browser
```

Credentials stored at `~/.local/share/autogenesis/auth.json` (0600 permissions).

**Token expired**

JWT tokens have `exp` claims. `is_token_expiring()` checks if < 5 min remaining. Re-login or configure auto-refresh.

**VM mode: credentials not available**

Gateway provider reads from `/run/autogenesis/credentials.json` (host-mounted). Verify:
```bash
cat /run/autogenesis/credentials.json
```

---

## §8: Database Issues

**"database is locked"**

Only one process should access each SQLite DB at a time. Check for:
- Multiple scheduler instances
- Orphaned processes: `pgrep -f autogenesis`

**Corrupt database**

```bash
# Check integrity
sqlite3 .autogenesis/ceo/ceo.db "PRAGMA integrity_check;"

# Nuclear option: delete and re-initialize
rm .autogenesis/ceo/ceo.db
# Next command will recreate it
```

**FTS5 index out of sync with brain.db**

If `brain_recall` returns wrong results:
```bash
sqlite3 .autogenesis/employees/{id}/brain.db "DELETE FROM memories_fts; INSERT INTO memories_fts (rowid, content, source, category) SELECT rowid, content, source, category FROM memories;"
```

---

## Quick Diagnostic Commands

```bash
# Test suite
uv run pytest packages/*/tests tests -q --tb=short

# Security checks
uv run ruff check --select S packages/
uvx pip-audit

# Check all employees
autogenesis hr list

# Check CEO state
autogenesis ceo status

# Check Twitter state
autogenesis twitter status

# Check config resolution
autogenesis config show

# Check gateway health (replace URL with your gateway_url)
curl -s http://127.0.0.1:1456/health | python -m json.tool

# List all databases
find .autogenesis -name "*.db" -ls
```
