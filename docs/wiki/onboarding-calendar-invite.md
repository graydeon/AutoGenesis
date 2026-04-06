# AutoGenesis Orientation Calendar Invite Bundle

**Owner:** `technical-writer`
**Audience:** `product-manager`, meeting host, and note-taker
**Status:** Ready pending confirmed date/time
**Last updated:** 2026-03-19

This bundle converts the [Onboarding Plan](onboarding-plan.md) into copy-ready scheduling assets. Fill in the placeholders after the Product Manager confirms the orientation date, time, timezone, and meeting link.

## Scheduling Inputs to Fill In

- **Date:** `{{DATE}}`
- **Start time:** `{{START_TIME}}`
- **End time:** `{{END_TIME}}`
- **Timezone:** `{{TIMEZONE}}`
- **Meeting URL / room:** `{{MEETING_URL_OR_ROOM}}`
- **Organizer:** `{{ORGANIZER_NAME}}`
- **Notes doc / recording hub:** `{{NOTES_URL}}`

## Required Attendees

- `product-manager`
- `cto`
- `technical-writer`
- `devops-engineer`
- `security-engineer`
- `frontend-engineer`
- `backend-engineer`
- `qa-engineer`
- `social-media-manager`

## Calendar Title

`AutoGenesis Employee Orientation + Introductions`

## Paste-Ready Calendar Description

```text
Welcome to AutoGenesis.

This 60-minute orientation aligns the team on mission, product context, tooling, security expectations, and immediate next steps so every employee leaves with confirmed access status and a named next action.

When
- Date: {{DATE}}
- Time: {{START_TIME}}–{{END_TIME}} {{TIMEZONE}}
- Location: {{MEETING_URL_OR_ROOM}}

Pre-work
- Read README.md
- Read HANDOFF.md
- Read docs/wiki/onboarding-packet.md
- Read docs/wiki/security-onboarding-module.md
- Review docs/wiki/onboarding-plan.md
- Skim docs/wiki/architecture.md and docs/wiki/employee-system.md
- Confirm access to the repo, terminal environment, docs, chat, calendar, and shared drives
- Prepare a 30–60 second introduction: role, focus area, current priority, and one question or blocker

Day-one expectations
- Join on time and ready to introduce yourself
- Bring any access blockers or setup questions
- Leave with a named owner for each blocker and a clear next step

Agenda
- 0:00–0:05 Welcome, meeting goal, success criteria, and norms
- 0:05–0:13 Mission, product direction, org context, engineering culture
- 0:13–0:18 Product walkthrough: end-user experience and core workflows
- 0:18–0:23 Technical overview: services, APIs, data flow, key docs
- 0:23–0:28 Access and tooling readiness review
- 0:28–0:33 Security setup, device hygiene, reporting paths
- 0:33–0:38 Quality expectations and dry-run findings
- 0:38–0:42 Brand voice and public communication norms
- 0:42–0:50 Round-robin introductions
- 0:50–1:00 Q&A, next steps, owners, and close

Reference docs
- README.md
- HANDOFF.md
- docs/wiki/onboarding-packet.md
- docs/wiki/security-onboarding-module.md
- docs/wiki/onboarding-plan.md
- docs/wiki/architecture.md
- docs/wiki/employee-system.md
- docs/wiki/cli-reference.md
- docs/wiki/config.md
- docs/wiki/troubleshooting.md

Shared artifacts
- Notes / recording hub: {{NOTES_URL}}
```

## Short Invite Version

```text
AutoGenesis orientation and introductions. Please complete the pre-work in README.md, HANDOFF.md, docs/wiki/onboarding-packet.md, docs/wiki/security-onboarding-module.md, and docs/wiki/onboarding-plan.md before the meeting. Come ready with a 30–60 second intro plus any access blockers. Goal: leave with confirmed access status, core-doc familiarity, a named next step, and a live owner for every immediate blocker.
```

## 24-Hour Reminder Message

```text
Reminder: AutoGenesis orientation is tomorrow at {{START_TIME}} {{TIMEZONE}}. Before we start, please read README.md, HANDOFF.md, docs/wiki/onboarding-packet.md, docs/wiki/security-onboarding-module.md, and docs/wiki/onboarding-plan.md; verify your repo/docs/chat/calendar access; and prepare a 30–60 second intro plus one blocker or question.
```

## Included Asset

- [`docs/wiki/onboarding-orientation-invite.ics.tmpl`](onboarding-orientation-invite.ics.tmpl) — placeholder `.ics` template for calendar systems that accept file imports

## Host Checklist

1. Replace all `{{...}}` placeholders.
2. Convert repo-relative doc paths to full GitHub or shared-doc URLs if your calendar client does not preserve Markdown links.
3. Attach or link the notes hub before sending.
4. Verify the attendee list matches the current roster in the onboarding plan.
5. Send the 24-hour reminder after the invite is accepted.
