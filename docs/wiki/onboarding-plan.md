# Employee Onboarding Plan

**Owner:** `product-manager`
**Status:** Scheduled for **Tuesday, March 24, 2026, 10:00–11:00 AM Central Time**
**Roster source:** active employee configs in `~/.config/autogenesis/employees/`
**Roster validation:** `uv run autogenesis hr list` confirmed **9 active employees** on **2026-03-19**. No project override YAMLs were present in `.autogenesis/employees/`.

## Orientation Logistics

- **Session:** AutoGenesis employee orientation
- **Date:** Tuesday, March 24, 2026
- **Time:** 10:00–11:00 AM Central Time (`America/Chicago`)
- **Duration:** 60 minutes
- **Planning DRI:** `product-manager`
- **Live host:** `cto`
- **Notes owner:** `technical-writer`
- **Live runbook:** [Onboarding Orientation Runbook](onboarding-orientation-runbook.md)
- **Live notes template:** [Onboarding Orientation Notes Template](onboarding-orientation-notes-template.md)

## Meeting Goal

Align the full AutoGenesis team on mission, product context, tools, security expectations, and first-week ways of working so every employee leaves the session with confirmed access, a clear owner map, and an actionable next step.

## Confirmed Attendees and Owners

All 9 active employees are required and confirmed for the orientation.

| Employee ID | Title | Attendance | Confirmed owner / session responsibility |
|---|---|---:|---|
| `product-manager` | Product Manager | Confirmed | Own the plan, send the invite, confirm attendance, support timekeeping, and track follow-ups |
| `cto` | CTO / Lead Architect | Confirmed | Host the live session, present mission and product direction, lead introductions, and drive blocker triage |
| `technical-writer` | Technical Writer | Confirmed | Publish onboarding packet, open shared notes, and maintain the follow-up hub |
| `devops-engineer` | DevOps / Infra Engineer | Confirmed | Verify baseline access, tooling, and shared systems |
| `security-engineer` | Security Engineer | Confirmed | Cover MFA, secrets handling, device expectations, and incident reporting |
| `frontend-engineer` | Frontend Engineer | Confirmed | Demo the user-facing product experience and core workflows |
| `backend-engineer` | Backend Engineer | Confirmed | Explain core services, APIs, data flow, and key technical docs |
| `qa-engineer` | QA / Test Engineer | Confirmed | Dry-run the onboarding flow and report gaps before the session |
| `social-media-manager` | Social Media Manager | Confirmed | Explain brand voice, announcement norms, and public escalation paths |

## Required Pre-Work

Complete all shared and role-specific pre-work by **Monday, March 23, 2026, 5:00 PM Central Time**.

### Shared for all employees

1. Read `docs/wiki/onboarding-packet.md`.
2. Read `docs/wiki/security-onboarding-module.md`.
3. Read `HANDOFF.md`.
4. Read `docs/wiki/architecture.md` and `docs/wiki/employee-system.md`.
5. Run `uv sync --all-packages` and `uv run autogenesis hr list`, then confirm access to the repository, terminal environment, docs, chat, calendar, and shared drives.
6. Prepare a 30–60 second introduction: role, focus area, current priority, and one question or blocker.
7. Submit any missing-access or setup blockers before end of day on **Monday, March 23, 2026**.

### Role-specific

- `product-manager`: send the calendar invite for **Tuesday, March 24, 2026, 10:00–11:00 AM CT**, finalize the agenda, set the intro order, and prepare the follow-up tracker.
- `technical-writer`: publish the packet, notes template, and link hub; confirm note-taking coverage.
- `devops-engineer`: complete the access matrix and verify all shared systems.
- `security-engineer`: publish the mandatory security onboarding module plus the day-one checklist and escalation paths.
- `cto`: prepare the mission, product, and culture overview using `docs/wiki/cto-orientation-segment.md`; own live facilitation, segment handoffs, and blocker triage during the session.
- `frontend-engineer`: prepare a concise live product walkthrough.
- `backend-engineer`: prepare a high-level technical architecture walkthrough and publish the short reference in `docs/wiki/backend-walkthrough.md`.
- `qa-engineer`: dry-run links, demos, and meeting flow; log gaps before kickoff.
- `social-media-manager`: prepare a short communications and brand briefing.

## Onboarding Checklist

| When | Owner | Checklist item |
|---|---|---|
| Thu, Mar 19, 2026 (T-3 business days) | Product Manager | Confirm roster, attendance, and meeting time |
| Fri, Mar 20, 2026 (T-2 business days) | DevOps / Infra Engineer | Provision and verify repo, docs, calendar, chat, and dashboard access |
| Fri, Mar 20, 2026 (T-2 business days) | Security Engineer | Confirm password manager, MFA, secrets-handling setup, and security-module distribution |
| Mon, Mar 23, 2026 (T-1 business day) | Technical Writer + Product Manager | Send onboarding packet, agenda, and pre-work links |
| Mon, Mar 23, 2026 (T-1 business day) | CTO / Frontend / Backend / Social | Finalize presentation materials and demos |
| Mon, Mar 23, 2026 (T-1 business day) | QA / Test Engineer | Dry-run the full flow and log any broken links or access gaps |
| Tue, Mar 24, 2026 (Day of) | Product Manager | Confirm attendance, intro order, note-taker, and follow-up tracker |
| Tue, Mar 24, 2026 (Day of) | Technical Writer | Open shared notes doc and publish meeting artifacts location |
| Wed, Mar 25, 2026 (Within 1 business day after) | Technical Writer + assigned owners | Publish notes, FAQs, next steps, and resolve open access issues |

## 60-Minute Agenda

| Time | Topic | Owner |
|---|---|---|
| 0:00–0:05 | Welcome, meeting goal, success criteria, norms, and host framing | CTO / Lead Architect + Product Manager |
| 0:05–0:13 | Mission, product direction, org context, engineering culture | CTO / Lead Architect |
| 0:13–0:18 | Product walkthrough: end-user experience and core workflows | Frontend Engineer |
| 0:18–0:23 | Technical overview: services, APIs, data flow, key docs, and backend reliability watch-outs | Backend Engineer |
| 0:23–0:28 | Access and tooling readiness review | DevOps / Infra Engineer |
| 0:28–0:33 | Security setup, device hygiene, reporting paths | Security Engineer |
| 0:33–0:38 | Quality expectations and dry-run findings | QA / Test Engineer |
| 0:38–0:42 | Brand voice and public communication norms | Social Media Manager |
| 0:42–0:50 | CTO-led round-robin introductions (30–60 seconds each) | All employees |
| 0:50–1:00 | Q&A, immediate blockers, owners, and close | CTO / Product Manager + Technical Writer |

Use the [Onboarding Orientation Runbook](onboarding-orientation-runbook.md) for the exact live host script, intro order, and segment handoffs for **Tuesday, March 24, 2026**.

Backend onboarding reference: [Backend Walkthrough](backend-walkthrough.md).

## Exit Criteria

- Every employee has confirmed baseline access or has a named owner for each blocker.
- Every employee knows the team roster, who owns what, and where core docs live.
- Security expectations, the incident path, and the security onboarding module have been acknowledged.
- Notes, packet links, and post-meeting action items are published in a shared hub.
