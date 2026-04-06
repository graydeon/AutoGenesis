# AutoGenesis Onboarding Orientation Runbook

**Owner:** `cto`
**Supports:** AutoGenesis employee orientation on **Tuesday, March 24, 2026, 10:00–11:00 AM Central Time**
**Planning DRI:** `product-manager`
**Notes owner:** `technical-writer`

This runbook is the live facilitation guide for the March 24 orientation. It keeps the meeting tight, makes the role-by-role introductions predictable, and protects the final 10 minutes for Q&A plus immediate blocker triage.

Primary presenter material for the CTO segment: [CTO Orientation Segment](cto-orientation-segment.md).

Live notes template: [Onboarding Orientation Notes Template](onboarding-orientation-notes-template.md).

## Day-of Roles

| Role | Employee | Responsibility during the live session |
|---|---|---|
| Live host | `cto` | Open the meeting, keep time, frame each segment, lead introductions, and drive blocker triage |
| Planning DRI / follow-up owner | `product-manager` | Confirm attendance, track action items, assign follow-ups, and close with next steps |
| Notes owner | `technical-writer` | Capture notes, decisions, open blockers, owners, and links to follow-up artifacts |
| Timebox support | `product-manager` | Give 1-minute warnings so handoffs stay on schedule |

## Success Criteria for the Live Session

By 11:00 AM Central Time on **Tuesday, March 24, 2026**, the team should have:

1. Met every active employee and heard each person's role, current priority, and one question or blocker.
2. Confirmed who owns each core onboarding area: product, architecture, docs, infra, security, quality, and public communications.
3. Logged every immediate blocker with a named owner and next action.
4. Left with a clear path for first-week work, follow-ups, and doc locations.

## Five-Minute Preflight (9:55–10:00 AM CT)

Complete these checks before admitting the group:

- `technical-writer` opens the shared notes doc using the [Onboarding Orientation Notes Template](onboarding-orientation-notes-template.md) and keeps the blocker tracker visible.
- `product-manager` confirms attendance and the speaking order.
- `frontend-engineer`, `backend-engineer`, `devops-engineer`, `security-engineer`, `qa-engineer`, and `social-media-manager` each have their materials open and ready.
- `cto` reminds presenters to stay inside the published timeboxes so the final 10 minutes remain protected.
- If a presenter is missing, `cto` gives a short placeholder summary and `product-manager` records the follow-up owner.

## 60-Minute Live Run of Show

| Time | Segment | Owner | CTO host cue / handoff |
|---|---|---|---|
| 10:00–10:05 AM | Welcome, goal, success criteria, norms | `cto` + `product-manager` | “Welcome to AutoGenesis orientation for Tuesday, March 24, 2026. Our goal today is simple: leave with context, clear ownership, and named owners for every blocker.” |
| 10:05–10:13 AM | Mission, product direction, org context, engineering culture | `cto` | “I’ll start with why AutoGenesis exists, how the system is organized, and how we make technical decisions.” |
| 10:13–10:18 AM | Product walkthrough | `frontend-engineer` | “Next, `frontend-engineer` will ground us in the end-user flow and what the product feels like in practice.” |
| 10:18–10:23 AM | Technical overview | `backend-engineer` | “From there, `backend-engineer` will connect the user experience to the core services, APIs, and data flow.” |
| 10:23–10:28 AM | Access and tooling readiness | `devops-engineer` | “`devops-engineer`, please walk us through baseline access, shared systems, and anything the team should validate today.” |
| 10:28–10:33 AM | Security setup and reporting paths | `security-engineer` | “`security-engineer`, cover the non-negotiables: MFA, secrets handling, device hygiene, and how to escalate incidents.” |
| 10:33–10:38 AM | Quality expectations and dry-run findings | `qa-engineer` | “`qa-engineer`, share what you validated in the dry run and where we should expect friction.” |
| 10:38–10:42 AM | Brand voice and public escalation norms | `social-media-manager` | “`social-media-manager`, close the functional briefings with our public voice, announcement norms, and escalation boundaries.” |
| 10:42–10:50 AM | Role-by-role introductions | All employees, led by `cto` | “We’ll go around in role order. Keep it to 30–60 seconds: role, focus area, current priority, and one question or blocker.” |
| 10:50–11:00 AM | Q&A, immediate blockers, owners, and close | `cto` + `product-manager` + `technical-writer` | “We’re holding the final 10 minutes for open questions and anything that blocks work this week. If it blocks work, we name an owner before we leave.” |

## Role-by-Role Introduction Order

Keep this order so the round-robin is predictable and aligned with the onboarding docs:

1. `cto`
2. `product-manager`
3. `technical-writer`
4. `frontend-engineer`
5. `backend-engineer`
6. `devops-engineer`
7. `security-engineer`
8. `qa-engineer`
9. `social-media-manager`

### Prompt for each introduction

Use the same prompt for every person:

- Your role and what you own
- Your current priority this week
- One question, risk, or blocker the team should know about

### CTO transition into introductions

Use this line verbatim or close to it:

“Let’s do introductions in role order. Please keep it short and concrete: what you own, what you’re focused on this week, and one question or blocker. If a blocker needs follow-up, we’ll capture the owner live instead of debating it now.”

## Blocker Capture Rules

During introductions and Q&A, sort blockers into one of these buckets immediately:

| Blocker type | Primary owner | Backup / escalation |
|---|---|---|
| Repo, environment, dashboard, or access issue | `devops-engineer` | `product-manager` |
| MFA, credentials, secrets, device, or policy issue | `security-engineer` | `cto` |
| Architecture, service boundaries, technical tradeoff | `cto` | `backend-engineer` |
| Product scope, priorities, onboarding workflow gaps | `product-manager` | `cto` |
| Documentation or missing reference material | `technical-writer` | `product-manager` |
| Quality, repro steps, or flow validation gap | `qa-engineer` | `frontend-engineer` / `backend-engineer` |
| Public messaging or external communication risk | `social-media-manager` | `product-manager` |

Rules for triage:

1. If the issue blocks work in the next 24 hours, assign the owner live before moving on.
2. If the issue needs investigation but does not block day-one work, log it in notes with an owner and target follow-up date.
3. If the issue is informational only, park it in the FAQ section of the notes doc.

## Close Script

Use a short close so the meeting ends with explicit ownership:

1. `technical-writer` reads back the open blockers and owners.
2. `product-manager` states the next checkpoint and where notes will live.
3. `cto` closes with: “If you still have an unresolved blocker after this call, raise it today, March 24, 2026, and tag the named owner. We optimize for fast escalation, not silent waiting.”

## After the Meeting

Within one business day after the session:

- `technical-writer` publishes notes, FAQs, and follow-up links using the completed [Onboarding Orientation Notes Template](onboarding-orientation-notes-template.md) as the source of truth.
- `product-manager` checks that every blocker has an owner and due date.
- `cto` follows up on any unresolved architecture or cross-team dependency issues.
