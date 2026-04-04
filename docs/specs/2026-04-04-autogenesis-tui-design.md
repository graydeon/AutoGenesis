# AutoGenesis TUI — Design Spec

**Date:** 2026-04-04
**Status:** Approved

---

## Overview

A custom Textual-based terminal UI for AutoGenesis that replaces the raw `codex` chat interface. The TUI provides a three-column Command Center layout with live employee status, streaming agent output, goal tracking, token metering, and full theme customization. It still uses `codex app-server` for inference and tool execution — the TUI owns only the presentation and interaction layer.

---

## 1. Package Structure

New workspace package: `packages/tui` (`autogenesis-tui`), added to `pyproject.toml` workspace members.

```
packages/tui/
  pyproject.toml
  src/autogenesis_tui/
    app.py              # AutogenesisApp — root Textual app, lifecycle
    server.py           # AppServerManager — spawns/kills codex app-server subprocess
    client.py           # CodexWSClient — WebSocket JSON-RPC to app-server
    themes.py           # ThemeManager — loads built-in + user TOML themes, applies CSS vars
    widgets/
      __init__.py
      roster.py         # EmployeeRoster — left column
      stream.py         # AgentStream — center column
      right_panel.py    # RightPanel — goals/tokens or employee detail
      input_bar.py      # InputBar — target dropdown + text input
      status_bar.py     # StatusBar — title, connection, model, tokens
```

**Dependencies** (added to `packages/tui/pyproject.toml`):
- `textual>=0.70`
- `websockets>=13`
- `tomllib` (stdlib in Python 3.11+)
- `autogenesis-core` (workspace)
- `autogenesis-employees` (workspace)

**CLI integration:** `autogenesis tui` command added to `packages/cli/app.py`. Imports `AutogenesisApp` from `autogenesis_tui.app`, calls `app.run()`.

---

## 2. Layout

Command Center: three columns, status bar top, input bar bottom.

```
┌─────────────────────────────────────────────────────────────────┐
│ StatusBar   ⬡ AutoGenesis  model  connection-state  token-count │
├──────────────┬──────────────────────────────┬───────────────────┤
│EmployeeRoster│        AgentStream           │    RightPanel     │
│              │                              │                   │
│ ● backend    │ [ALL] [CEO] [frontend-eng ✕] │  Goals / Tokens   │
│ ▶ frontend   │                              │  — or —           │
│ ⟳ analyst   │  CEO › decomposing...        │  Employee Detail  │
│ ○ devops     │  frontend › Reading file     │  (brain + inbox)  │
│ ○ qa         │    ▸ file_read Auth.tsx       │                   │
│              │  frontend › Writing file...  │                   │
│ SHORTCUTS    │    ▸ file_write Auth.tsx      │                   │
│ H S U ?      │  frontend › ✓ done           │  ← back to goals  │
├──────────────┴──────────────────────────────┴───────────────────┤
│ InputBar  [ CEO ▾ ]  type a message...                   Enter ↵ │
└─────────────────────────────────────────────────────────────────┘
```

**Theme:** Dracula by default (configurable). See Section 5.

---

## 3. Architecture & Data Flow

### 3.1 Startup sequence

1. `AutogenesisApp.on_mount()` calls `AppServerManager.start()`
2. `AppServerManager` spawns: `codex app-server --listen ws://127.0.0.1:<PORT> --dangerously-bypass-approvals-and-sandbox`
3. Port is selected by binding a socket to port 0 (OS assigns a free port); passed to `CodexWSClient`
4. `CodexWSClient` connects, sends `initialize`, then `thread/start` with CEO system prompt
5. `EmployeeRoster` loads from `EmployeeRegistry` (disk)
6. Event bus subscriptions registered for `CEO_SUBTASK_ASSIGN`, `CEO_SUBTASK_COMPLETE`, `CEO_SUBTASK_FAIL`, `CEO_ESCALATION`
7. On exit: `AppServerManager.stop()` terminates the subprocess

### 3.2 Two data sources for AgentStream

**Source 1 — WebSocket (`CodexWSClient`):**
Handles the interactive CEO chat session. Relevant events:

| Event | Rendered as |
|-------|-------------|
| `item/agentMessage/delta` | Streaming agent text, tagged `CEO` or active employee |
| `item/commandExecution/outputDelta` | Indented tool block with left-border in employee color |
| `turn/started` | Dim separator line |
| `turn/completed` | ✓ marker |
| `thread/tokenUsage/updated` | Updates token meter in StatusBar and RightPanel |

**Source 2 — Event bus + SubAgentManager `on_output`:**
Handles output from `ceo run` / `ceo dispatch` employee subprocesses. The `SubAgentManager` `on_output` callback is wired to post a Textual message to `AgentStream`, tagged with the dispatched employee's ID. Event bus subscriptions update `EmployeeRoster` status indicators (idle → working → done).

### 3.3 Input routing

The `InputBar` dropdown has two modes:

- **CEO (default):** Input sent as `turn/start` via WebSocket to the active app-server thread. Plain messages go as chat; `/run <goal>` or `Ctrl+G` triggers `CEOOrchestrator.run()` in an async task.
- **Employee selected:** Opens a new app-server thread (`thread/start`) with that employee's system prompt injected. Stream and right panel both switch context to that employee. Switching back to CEO resumes the original thread.

### 3.4 Employee detail (RightPanel)

When an employee is selected in the roster:
- RightPanel switches from Goals/Tokens view to Employee Detail view
- `BrainManager.top_memories(10)` fetched async → displayed as bullet list
- `InboxManager.get_unread(employee_id)` fetched async → displayed as message cards
- Training directives pulled from `EmployeeConfig`
- "← back to goals" link or `Esc` returns to default view

AgentStream simultaneously sets the active filter chip to that employee, showing only their messages and tool calls.

---

## 4. Widgets

### StatusBar
Top bar. Shows: app name, active model (from `thread/started` event), WebSocket connection state (connecting / connected / reconnecting), session token count (updated from `thread/tokenUsage/updated`).

### EmployeeRoster
Left column. Scrollable list of employees from `EmployeeRegistry`. Each row shows: status indicator (● idle / ⟳ working / ✓ done / ○ offline), employee ID, current activity (truncated, updated via `on_output`). Keyboard shortcut section at bottom. Clicking or pressing Enter selects/deselects an employee.

### AgentStream
Center column. Scrolling log of all agent activity. Filter chips at top: `ALL`, `CEO`, one chip per employee that has produced output this session. Each entry is color-coded by source employee. Tool calls rendered as indented blocks with a left border in the employee's color:

```
frontend-eng › Writing Auth.tsx...
  ▸ file_write  src/components/Auth.tsx
  → written successfully
```

Auto-scrolls to bottom; stops auto-scroll if user scrolls up (resumes on `G` or new input).

### RightPanel
Right column. Two modes:

**Default (Goals/Tokens):**
- Active goals list with progress bars (subtasks completed / total), sourced from `CEOStateManager`
- Token budget meters: session tokens (from WebSocket events), daily total (from `autogenesis_tokens` budget tracker)
- Queued tasks count

**Employee Detail:**
- Employee name + status header
- Brain memories (top 10, from `BrainManager`)
- Unread inbox messages (from `InboxManager`)
- Training directives (from `EmployeeConfig`)
- "← back to goals" footer

### InputBar
Bottom bar. Two components:
- **Dropdown** (`Ctrl+Space` or click): lists CEO + all employees with status indicators. Arrow keys + Enter to select. Selected target shown in employee's accent color.
- **Text input**: placeholder text reflects active target. `Enter` submits. `Ctrl+C` sends `turn/interrupt`.

### Employee accent colors
Each employee is assigned a color by cycling through a fixed palette derived from the active theme's accent, success, warning, error, and text values. Assignments are stable within a session (index into palette by roster order). The CEO always uses the theme's `accent` color.

---

## 5. Theme System

### Built-in themes
Three themes ship with the package:
- `dracula` (default) — purple/pink/green on near-black
- `midnight-blue` — GitHub-dark inspired, blue accents
- `hacker-green` — phosphor green on deep black

### Custom themes
Drop a TOML file into `~/.config/autogenesis/themes/` to add it to the picker.

**Theme file format:**
```toml
name = "My Theme"
background = "#1e1e2e"
surface    = "#181825"
accent     = "#cba6f7"
success    = "#a6e3a1"
warning    = "#f9e2af"
error      = "#f38ba8"
text       = "#cdd6f4"
subtext    = "#6c7086"
border     = "#45475a"
```

### ThemeManager
`ThemeManager` scans built-in themes (bundled in `autogenesis_tui/themes/`) and user themes (`~/.config/autogenesis/themes/`). Exposes `list_themes()` and `apply(theme_name, app)`. Applying a theme writes Textual CSS variable overrides and calls `app.refresh_css()` — no restart required.

### Configuration
`tui.theme` key in the standard config cascade. Default: `dracula`. Selected theme persists when changed via the `T` picker.

**Config example:**
```yaml
tui:
  theme: dracula
```

---

## 6. Key Bindings

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate employee roster |
| `Enter` | Select / deselect employee |
| `Esc` | Deselect employee, return to ALL stream + goals panel |
| `Tab` | Cycle focus: roster → stream → input |
| `Ctrl+G` | New goal prompt → `CEOOrchestrator.run()` |
| `Ctrl+N` | New app-server thread (`thread/start`) |
| `Ctrl+C` | Interrupt active turn (`turn/interrupt`) |
| `T` | Theme picker overlay |
| `H` | HR command palette |
| `S` | Run standup |
| `U` | Union proposals |
| `G` | Jump AgentStream to bottom |
| `?` | Help overlay |

---

## 7. Error Handling

- **App-server fails to start:** StatusBar shows "disconnected" in error color; TUI remains open and retries every 5s.
- **WebSocket disconnects:** `CodexWSClient` attempts reconnect with exponential backoff (1s, 2s, 4s, max 30s). StatusBar shows "reconnecting...".
- **Employee subprocess timeout:** Shown as a `⚠ timed out` entry in AgentStream for that employee; event bus emits `CEO_SUBTASK_FAIL`.
- **No employees hired:** EmployeeRoster shows a prompt: "No employees — press H to hire".

---

## 8. Out of Scope

- Twitter agent panel (can be added later as a RightPanel tab)
- Multi-window / split terminal sessions
- Mouse-driven text selection in AgentStream (terminal limitation)
- Light mode (can be added as a theme TOML)
- Remote TUI (connecting to app-server on another machine)
