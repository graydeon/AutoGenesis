# AutoGenesis Security Onboarding Module

**Owner:** `security-engineer`
**Audience:** All AutoGenesis employees
**Status:** Active baseline; original March 2026 orientation deadline is archived
**Estimated read time:** 5 minutes
**Last updated:** 2026-04-24

This module is the minimum day-one security baseline for every AutoGenesis employee. For future onboardings, complete it before your orientation session alongside the onboarding packet and plan. The Security Engineer should review highlights during orientation, but everyone is expected to arrive having already read and applied the checklist below.

## Mandatory Acknowledgement

By joining AutoGenesis, you are agreeing to all of the following:

- I use unique passwords stored in an approved password manager.
- I enable MFA on every company account that supports it.
- I never place real secrets in Git, docs, tickets, chat, screenshots, prompts, or demos.
- I request only the access I need and never share accounts, sessions, or tokens.
- I report suspected incidents, exposed secrets, lost devices, or suspicious access immediately.

## 1. Account Hygiene

- Use long, unique, password-manager-generated passwords for every company system.
- MFA is required for GitHub, email, chat, calendar, the password manager, cloud/admin consoles, and any tool with repo, credential, or production access.
- Keep screen lock, full-disk encryption, and automatic security updates enabled on work devices.
- Do not use shared, borrowed, or unmanaged devices for company work unless explicitly approved.
- Report lost or stolen devices, unexpected MFA prompts, and suspicious sign-in alerts immediately.

## 2. Secrets Handling

- Never commit, paste, or upload real secrets to the repo, docs, changelogs, tickets, PRs, chat, screenshots, or AI prompts.
- AutoGenesis default: the **host machine holds real secrets**; agents and VMs should receive only scoped tokens or mounted runtime credentials.
- Store secrets only in approved secret managers, environment injection paths, or runtime-mounted files.
- In docs, tests, demos, and examples, use fake placeholders such as `YOUR_TOKEN_HERE` or obviously sanitized values.
- Before sharing logs or screenshots, remove tokens, cookies, authorization headers, credential files, and customer data.
- If a secret is exposed or may have been exposed, revoke or rotate it as soon as it is safe to do so, then report the incident.

## 3. Access Rules

- Follow least privilege: request only the systems, roles, and scopes needed for the task at hand.
- Access is personal and non-transferable. Never share logins, MFA codes, session cookies, API tokens, or local credential files.
- Production systems and customer or sensitive data require an approved business need and a named owner.
- Do not connect new SaaS tools, OAuth apps, MCP servers, browser extensions, or automations that can read or write company data without owner approval.
- Remove or downgrade temporary elevated access when the task is complete, and flag stale access when you notice it.

## 4. Incident Reporting

Report suspected security incidents within **15 minutes** of discovery.

### What counts as an incident

- Exposed or mis-sent secret
- Suspicious login, MFA prompt, or account behavior
- Lost or stolen device
- Phishing, malware, or unexpected remote-access request
- Unauthorized access to code, systems, or data
- Accidental public posting of internal information
- Possible customer-data leak or third-party compromise

### Who to notify

1. Notify `security-engineer` immediately.
2. Include `devops-engineer` if infrastructure, credentials, deployments, or service availability may be affected.
3. Include `product-manager` if customer impact, release risk, or schedule impact is possible.

### What to include

- What happened
- When it happened or was discovered
- Which accounts, systems, repos, or secrets may be involved
- What containment actions have already been taken
- What is still unknown or needs help right now

### First-response rules

- Stop the spread first: revoke, rotate, isolate, or disable access if it is safe to do so.
- Preserve evidence: keep timestamps, screenshots, logs, links, and terminal output.
- Do not delete evidence or quietly fix-and-forget a security event.
- Do not discuss sensitive incidents in broad public channels before coordination.

## 5. Secure Collaboration Expectations

- Keep docs, changelogs, and handoffs useful, but never include real secrets or sensitive customer data.
- Use private channels for security-sensitive details; share sanitized summaries in general collaboration spaces.
- Ask for security review on changes involving auth, permissions, secrets, data handling, third-party access, or public-facing behavior.
- Respect approval boundaries: no public posting, destructive actions, production changes, or privilege expansion without the required owner approval.
- Leave clean handoffs with changed files, risk notes, test status, and any follow-up or rollback considerations.

## Day-One Completion Checklist

Complete all items before orientation:

- [ ] Password manager is configured and in active use.
- [ ] MFA is enabled everywhere it is available for company accounts.
- [ ] I know where secrets may live and where they must never appear.
- [ ] I know the 15-minute incident-reporting rule and the first contacts.
- [ ] I will raise any remaining security blocker before my orientation session or first assigned task.
