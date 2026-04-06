# AutoGenesis Employee Welcome Packet

**Owner:** `technical-writer`
**Audience:** New and existing AutoGenesis employees
**Status:** Active
**Last updated:** 2026-03-19

This welcome packet is the published day-one hub for the current onboarding docs set. It pulls together the [README](../../README.md), [Handoff](../../HANDOFF.md), [Onboarding Plan](onboarding-plan.md), orientation agenda, and the key links each employee needs before the live session on **Tuesday, March 24, 2026, 10:00–11:00 AM Central Time**.

## Start Here

1. Read the [README](../../README.md) for install, quick start, and the package map.
2. Read the [Handoff](../../HANDOFF.md) for current state, quick commands, and architectural decisions.
3. Review the [Onboarding Plan](onboarding-plan.md) for the roster, agenda, and pre-work expectations.
4. Read the [Security Onboarding Module](security-onboarding-module.md) for the mandatory account, secrets, access, and incident baseline.
5. Skim [Architecture](architecture.md) and [Employee System](employee-system.md) so the org model and system boundaries feel familiar.
6. Confirm access to the repository, terminal environment, docs, chat, calendar, and shared drives.
7. Prepare a 30–60 second introduction: role, focus area, current priority, and one question or blocker.
8. Raise missing-access or setup blockers before the orientation begins.

## Orientation Snapshot

| Item | Details |
|---|---|
| Session | AutoGenesis employee orientation |
| Date | Tuesday, March 24, 2026 |
| Time | 10:00–11:00 AM Central Time (`America/Chicago`) |
| Host | `cto` |
| Planning DRI | `product-manager` |
| Notes owner | `technical-writer` |
| Source docs | [Onboarding Plan](onboarding-plan.md), [Orientation Runbook](onboarding-orientation-runbook.md), [Calendar Invite Bundle](onboarding-calendar-invite.md) |

### Meeting goal

Align the full AutoGenesis team on mission, product context, tooling, security expectations, and first-week ways of working so every employee leaves with confirmed access status, a clear owner map, and an actionable next step.

## Company Mission

AutoGenesis exists to turn high-level product goals into completed work through a structured team of specialized employees powered by OpenAI Codex. The system is designed to make multi-agent work reliable by combining clear roles, persistent memory, async coordination, human-readable plans, and explicit escalation when something fails.

### What we optimize for

- **Autonomous execution with human oversight**
- **Clear role ownership across the team**
- **Fast handoffs through shared memory, inboxes, and changelogs**
- **Simple, well-documented systems over hidden magic**

## Day-One Expectations

| Expectation | What “ready” looks like |
|---|---|
| Arrive with context | You have read `README.md`, `HANDOFF.md`, and this packet. |
| Arrive with access status | You know which tools and systems work, and you can name any blockers immediately. |
| Arrive ready to introduce yourself | You can give a short intro plus one current question, risk, or blocker. |
| Arrive ready to navigate the docs | You know where onboarding, architecture, employee-system, and CLI docs live. |
| Leave with ownership | You leave the session with a named next step and a named owner for each unresolved blocker. |

## Simple Day-One Checklist

### Every employee

- [ ] Read [README](../../README.md), [Handoff](../../HANDOFF.md), this packet, and the [Security Onboarding Module](security-onboarding-module.md).
- [ ] Review the [Onboarding Plan](onboarding-plan.md), [Architecture](architecture.md), and [Employee System](employee-system.md).
- [ ] Run `uv sync --all-packages`.
- [ ] Run `uv run autogenesis hr list`.
- [ ] Confirm access to the repo, terminal environment, docs, chat, calendar, and shared drives.
- [ ] Prepare a 30–60 second introduction with your role, focus area, current priority, and one question or blocker.
- [ ] Raise any missing-access or setup blocker before **Monday, March 23, 2026, 5:00 PM Central Time**.

### Role-specific day-one checklist

| Employee | Simple checklist |
|---|---|
| `product-manager` | Confirm the invite, attendee list, intro order, and follow-up tracker; support timekeeping during the session. |
| `cto` | Host the session, cover mission and product direction, lead introductions, and assign owners for blockers. |
| `technical-writer` | Publish this packet, open the shared notes doc, capture decisions and blockers, and publish follow-up links. |
| `devops-engineer` | Verify repo, docs, chat, calendar, dashboard, and environment access; confirm shared tooling works. |
| `security-engineer` | Review MFA, password-manager, secrets-handling, device-hygiene, and incident-reporting expectations. |
| `frontend-engineer` | Prepare a short product walkthrough covering the end-user flow and core UX. |
| `backend-engineer` | Prepare a short architecture walkthrough covering services, APIs, data flow, and backend docs. |
| `qa-engineer` | Dry-run the onboarding flow, verify links and demos, and surface any friction before kickoff. |
| `social-media-manager` | Prepare the brand voice, announcement norms, and public escalation guidance for the team. |

## 60-Minute Orientation Agenda

| Time | Topic | Owner |
|---|---|---|
| 0:00–0:05 | Welcome, meeting goal, success criteria, norms, and host framing | `cto` + `product-manager` |
| 0:05–0:13 | Mission, product direction, org context, engineering culture | `cto` |
| 0:13–0:18 | Product walkthrough: end-user experience and core workflows | `frontend-engineer` |
| 0:18–0:23 | Technical overview: services, APIs, data flow, key docs, and backend reliability watch-outs | `backend-engineer` |
| 0:23–0:28 | Access and tooling readiness review | `devops-engineer` |
| 0:28–0:33 | Security setup, device hygiene, and reporting paths | `security-engineer` |
| 0:33–0:38 | Quality expectations and dry-run findings | `qa-engineer` |
| 0:38–0:42 | Brand voice and public communication norms | `social-media-manager` |
| 0:42–0:50 | Round-robin introductions | All employees |
| 0:50–1:00 | Q&A, immediate blockers, owners, and close | `cto` + `product-manager` + `technical-writer` |

For the live host script, intro order, and blocker-capture rules, use the [Onboarding Orientation Runbook](onboarding-orientation-runbook.md).

## Team Directory

| Employee ID | Title | Primary responsibility | Go to them for |
|---|---|---|---|
| `cto` | CTO / Lead Architect | Technical direction and architecture | System design, tradeoffs, long-term maintainability |
| `product-manager` | Product Manager | Requirements, prioritization, roadmap | Scope, priorities, acceptance criteria |
| `technical-writer` | Technical Writer | Docs, onboarding, reference material | READMEs, guides, onboarding, doc gaps |
| `backend-engineer` | Backend Engineer | Services, APIs, databases | Data flow, backend implementation, migrations |
| `frontend-engineer` | Frontend Engineer | UI, UX, React, TypeScript | Product walkthroughs, UX tradeoffs, frontend changes |
| `devops-engineer` | DevOps / Infra Engineer | CI/CD, infra, observability | Environments, deployment, service health, access |
| `security-engineer` | Security Engineer | Threat modeling and security review | Secrets, auth, risk review, incident escalation |
| `qa-engineer` | QA / Test Engineer | Quality strategy and coverage | Test plans, regressions, reproducibility |
| `social-media-manager` | Social Media Manager | Public voice and announcements | Launch messaging, brand voice, social feedback |

## Shared Tools

### Day-one environment

| Tool | Purpose |
|---|---|
| `uv` | Install dependencies and run workspace commands |
| `python` 3.11+ | Project runtime |
| `autogenesis` CLI | Main control plane for CEO, HR, meetings, union, and Twitter workflows |
| `pytest` | Run test suites |
| `ruff` | Lint and format Python code |
| Git + GitHub | Version control and collaboration |
| `docs/wiki/` | Primary documentation hub |

### Shared employee coordination tools

| Tool | Purpose |
|---|---|
| `brain_write` | Save durable decisions, patterns, and notes |
| `brain_recall` | Retrieve prior context from memory |
| `send_message` | Hand off work or ask another employee for help |
| `changelog_write` | Record completed work in the shared changelog |
| `standup_write` | Publish yesterday/today/blockers updates |
| `union_propose` | Raise cross-team process, tooling, or workload proposals |

### Useful starter commands

```bash
uv sync --all-packages
uv run autogenesis hr list
uv run autogenesis ceo status
uv run autogenesis standup
uv run python -m pytest packages/core/tests/ packages/employees/tests/ packages/tools/tests/ packages/cli/tests/ -v
```

## Key Links

| Link | Why it matters |
|---|---|
| [README](../../README.md) | Install, quick start, package map, and top-level project framing |
| [HANDOFF.md](../../HANDOFF.md) | Current project state, quick commands, and key architectural decisions |
| [Onboarding Plan](onboarding-plan.md) | Roster, pre-work, checklist, and orientation agenda |
| [Security Onboarding Module](security-onboarding-module.md) | Mandatory baseline for account hygiene, secrets, access, incident response, and secure collaboration |
| [Calendar Invite Bundle](onboarding-calendar-invite.md) | Copy-ready invite text, reminder text, and an `.ics` template |
| [Architecture](architecture.md) | Package map, data flow, and key classes |
| [Employee System](employee-system.md) | Roles, memory, inbox, changelog, meetings, and union workflows |
| [Backend Walkthrough](backend-walkthrough.md) | Short backend tour of services, APIs, state stores, and reliability concerns |
| [CTO Orientation Segment](cto-orientation-segment.md) | Mission, architecture, team interfaces, standards, and current technical priorities |
| [CLI Reference](cli-reference.md) | Command reference with examples |
| [Configuration](config.md) | Config layers, fields, and environment variables |
| [Troubleshooting](troubleshooting.md) | Common failure modes and recovery steps |

## Communication Norms

1. **Start with clarity.** Ask clarifying questions when scope, requirements, or constraints are ambiguous.
2. **Prefer concise async updates.** Use the changelog for completed work and messages for handoffs or blockers.
3. **Escalate blockers early.** Security, credential, infra, and production-risk issues should move fast.
4. **Leave a trail.** Record durable decisions in docs or memory so the next employee can continue without guesswork.
5. **Be explicit about ownership.** State the owner, files changed, test status, and next step in handoffs.
6. **Protect secrets and approval boundaries.** Credentials stay on the host; public posting still requires human approval.

## After the Orientation

1. Close any open access blockers with the named owner from the meeting.
2. Finish local setup with `uv sync --all-packages`.
3. Run a basic health check:
   - `uv run autogenesis hr list`
   - `uv run autogenesis ceo status`
   - `uv run python -m pytest packages/core/tests/ packages/employees/tests/ packages/tools/tests/ packages/cli/tests/ -v`
4. Bookmark the docs in the table above so you can re-enter context quickly.
5. Record any documentation gap or repeated setup issue so the packet can improve for the next employee.

## Important Working Paths

- `.autogenesis/changelog.md` — shared team activity log
- `.autogenesis/ceo/plans/` — human-readable goal plans
- `.autogenesis/employees/{employee_id}/` — per-employee memory and inbox state
- `packages/employees/templates/` — role templates and tool access
