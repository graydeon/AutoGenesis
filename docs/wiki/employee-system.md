# Employee System

## Overview

Subagents are modeled as startup employees with persistent state, inter-agent messaging, and collaboration tools.

## Core Employees (9 templates)

| ID | Title | Key Tools |
|----|-------|-----------|
| `cto` | Chief Technology Officer | shell, file_read, file_write, sub_agent |
| `frontend-engineer` | Frontend Engineer | shell, file_read, file_write, glob, grep |
| `backend-engineer` | Backend Engineer | shell, file_read, file_write, glob, grep |
| `devops-engineer` | DevOps Engineer | shell, file_read, file_write, bash |
| `qa-engineer` | QA Engineer | shell, file_read, file_write, glob, grep |
| `security-engineer` | Security Engineer | shell, file_read, grep, web_fetch |
| `technical-writer` | Technical Writer | file_read, file_write, glob |
| `product-manager` | Product Manager | file_read, think, ask_user |
| `social-media-manager` | Social Media Manager | twitter_browse, twitter_post, think |

Templates: `packages/employees/templates/*.yaml`

## Per-Employee State

Each employee gets isolated persistent state:

```
.autogenesis/employees/{employee_id}/
  brain.db    → SQLite + FTS5 memory (decisions, patterns, notes)
  inbox.db    → Async message queue from other employees
```

Shared state:
```
.autogenesis/changelog.md   → Team changelog (all employees write to this)
```

## Employee Config (YAML)

```yaml
id: backend-engineer
title: Backend Engineer
persona: "Expert Python developer focused on APIs, databases, and system design."
tools: [shell, file_read, file_write, glob, grep]
env: {}
training_directives:
  - "Always use type hints"
  - "Write tests before implementation"
status: active   # or "archived"
hired_at: "2026-03-19"
```

## HR Operations

| Operation | What happens |
|-----------|-------------|
| **Hire** | Creates YAML from template, sets id/title/status/hired_at |
| **Fire** | Sets `status: archived` in YAML (employee excluded from dispatch) |
| **Train** | Appends directive to `training_directives` list |

## System Prompt Construction

`EmployeeRuntime.build_system_prompt()` assembles:

1. **Role section** — title + persona + training directives + available tools
2. **Memory section** — top N memories from brain.db by relevance score
3. **Inbox section** — unread messages from other employees
4. **Changelog section** — recent N team activity entries
5. **Task section** — the current assigned task
6. **Standing instructions** — always write changelog, use brain_write, send_message, never reveal AI identity

## Built-in Employee Tools

| Tool | Purpose |
|------|---------|
| `brain_write` | Store a memory (category: decision/pattern/note/context) |
| `brain_recall` | FTS5 search through memories |
| `send_message` | Send async message to another employee |
| `changelog_write` | Document completed work |
| `standup_write` | Post daily standup update |
| `union_propose` | File a union proposal |

## Brain Memory System

- **Write**: Store with category, content, source, project
- **Recall**: FTS5 full-text search, boosts relevance to 1.0 on access
- **Decay**: `decay_all(factor=0.95)` — multiplicative daily decay
- **Prune**: Remove lowest-relevance when over limit (default 1000)
- **Top memories**: Sorted by relevance_score DESC, injected into system prompt

## Inter-Agent Messaging

Employees communicate asynchronously via inbox:
- `send_message(to, subject, body)` → creates InboxMessage in recipient's inbox.db
- Unread messages injected into system prompt on next dispatch
- Messages marked read after delivery

## Meetings

- **Standup**: Each employee dispatched with standup prompt, responses collected into `standup-{date}.md`
- **On-demand**: Employees dispatched with topic, responses collected into `meeting-{datetime}.md`
- Files written to `.autogenesis/meetings/`

## Union

- Employees file proposals (categories: hiring, tooling, process, architecture, workload)
- Votes: support / neutral / oppose (with optional comment)
- Proposals resolved by user: accepted / rejected / tabled
- `union review` dispatches all employees to vote on open proposals
