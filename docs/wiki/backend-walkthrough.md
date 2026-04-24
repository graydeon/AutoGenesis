# Backend Walkthrough

**Owner:** `backend-engineer`
**Audience:** New hires and engineers re-entering the codebase
**Status:** Active
**Last updated:** 2026-04-24

This is the short backend briefing for onboarding. AutoGenesis is **CLI-first**, so most backend boundaries are Python managers and subprocesses rather than a traditional long-running REST or GraphQL service. The two main external HTTP boundaries are the OpenAI Responses API and the host-local Twitter signing gateway.

## Backend Surface Area

| Area | Package | What it owns |
|---|---|---|
| Control plane | `packages/cli` | User-facing commands that invoke CEO, HR, Twitter, meeting, and config workflows |
| Orchestration | `packages/employees` | Goal decomposition, employee assignment, prompt assembly, persistent team state, and resume/escalation flows |
| Model execution | `packages/core` | OAuth, credential loading, SSE model client, agent loop, subprocess supervision, config, and events |
| Tooling layer | `packages/tools` | Employee tool implementations such as filesystem, bash, brain, messaging, changelog, and Twitter helpers |
| Twitter backend | `packages/twitter` | Feed browsing, draft queue, posting client, gateway, and session scheduling |

## APIs and Service Boundaries

- **Primary app interface:** the `autogenesis` CLI, not a public web API.
- **External model API:** `CodexClient` streams the OpenAI Responses API over SSE in `packages/core/src/autogenesis_core/client.py`.
- **Subprocess boundary:** `SubAgentManager` launches `codex exec` workers for CEO reasoning and employee execution in `packages/core/src/autogenesis_core/sub_agents.py`. It now defaults to approval-on-request plus workspace-write sandbox; unsafe bypass requires explicit opt-in.
- **Host auth boundary:** `packages/core/src/autogenesis_core/auth.py` handles PKCE OAuth on the host and stores tokens at `~/.local/share/autogenesis/auth.json` with `0600` permissions.
- **Local HTTP boundary:** `packages/twitter/src/autogenesis_twitter/gateway.py` runs on `127.0.0.1:1456` and signs tweet requests so agent workspaces never receive raw Twitter credentials.
- **In-process event API:** `EventBus` publishes lifecycle events for loops, tools, employees, CEO orchestration, and Twitter flows.

## Main Databases and State Files

| Store | Location | Purpose |
|---|---|---|
| `ceo.db` | `.autogenesis/ceo/ceo.db` | Goal queue, standalone task queue, and execution history |
| Goal plans | `.autogenesis/ceo/plans/goal-*.md` | Human-readable plan state and resume markers |
| `brain.db` | `.autogenesis/employees/{employee_id}/brain.db` | Per-employee durable memory with FTS5 recall |
| `inbox.db` | `.autogenesis/employees/{employee_id}/inbox.db` | Async handoff queue between employees |
| Team changelog | `.autogenesis/changelog.md` | Append-only shared activity log used as prompt context |
| `union.db` | `$XDG_STATE_HOME/autogenesis/union/{project}/union.db` | Union proposals and votes |
| `twitter_queue.db` | `$XDG_STATE_HOME/autogenesis/twitter_queue.db` or configured path | Draft, approved, posted, rejected, and failed tweet state |

## Core Data Flows

### 1. CEO goal execution

1. A user runs `autogenesis ceo run "..."`.
2. `CEOOrchestrator` decomposes the goal and assigns employees.
3. The orchestrator writes goal metadata to `ceo.db` and a markdown plan under `.autogenesis/ceo/plans/`.
4. `EmployeeRuntime` builds each employee prompt from role config, top brain memories, unread inbox messages, recent changelog entries, and the assigned task.
5. `SubAgentManager` spawns a Codex CLI subprocess to do the work.
6. Results are written back to `ceo.db` and the plan file. Failures get one retry with failure context, then escalate.

### 2. Direct agent loop

1. `AgentLoop` sends messages and tool definitions to `CodexClient`.
2. The model response streams back over SSE.
3. Tool calls are parsed, executed, and appended to the conversation.
4. The loop repeats until the model stops calling tools or `max_iterations` is hit.

### 3. Twitter posting path

1. `TwitterScheduler` checks permission and active hours.
2. The browser gathers feed items and the pre-filter narrows candidates.
3. Approved drafts are read from `twitter_queue.db`.
4. `TwitterPoster` sends an unsigned request to the local gateway.
5. The gateway signs and forwards the request to Twitter, then the queue is marked `posted` or `failed`.

## Reliability and Data-Flow Concerns New Hires Should Know

- **SQLite is the persistence backbone.** It keeps local state simple and durable, but it is still single-writer storage. Avoid long transactions and be careful with new concurrent write paths.
- **Goal state is split across SQLite and markdown.** `ceo.db` is the machine-readable record, while plan markdown is the human-readable resume surface. Debugging usually requires checking both.
- **In-flight execution is not fully durable yet.** Active subprocesses live in memory inside `SubAgentManager`, and execution rows are recorded after a subtask run returns. Treat `executions` as history, not as a true lease table for live work.
- **Failure handling is intentionally simple.** Default dispatch timeout is 300 seconds, each failed dispatch gets one retry, and then the system escalates instead of masking the failure.
- **The backend crosses several boundary types.** We mix direct SSE API calls, subprocess I/O, SQLite state, markdown files, and a local HTTP gateway. Contract drift across those boundaries is a common source of bugs.
- **Eventing is local-only.** `EventBus` is synchronous and in-process, which is great for hooks and tests but not durable telemetry or cross-process coordination.
- **Outbound side effects are not fully idempotent.** For example, tweet queue entries are marked `posted` only after a successful gateway call, so a crash in the middle of that path can leave room for duplicate retries.
- **Some packages are present but not in the live path yet.** `tokens`, `optimizer`, `security`, `mcp`, and `plugins` are scaffolded modules, so do not assume they already harden or observe the active execution path.

## Start Here in Code

- `packages/employees/src/autogenesis_employees/orchestrator.py`
- `packages/employees/src/autogenesis_employees/state.py`
- `packages/employees/src/autogenesis_employees/runtime.py`
- `packages/core/src/autogenesis_core/client.py`
- `packages/core/src/autogenesis_core/loop.py`
- `packages/core/src/autogenesis_core/sub_agents.py`
- `packages/twitter/src/autogenesis_twitter/queue.py`
- `packages/twitter/src/autogenesis_twitter/gateway.py`
