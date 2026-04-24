# Security Audit

**Date:** 2026-04-24
**Scope:** AutoGenesis local checkout, GitHub remote state, CI workflows, agent runtime boundaries, dependency posture, and public docs.

## Executive Summary

No known dependency CVEs were found and Ruff's security lint rules pass. The highest-risk issues from the initial audit have been mitigated in the local working tree: Codex subprocesses no longer default to approval/sandbox bypass, shell/filesystem tools now enforce workspace and command policies, and the Twitter gateway/poster contract has auth and schema tests. Remaining security work is concentrated around universal guardrail enforcement, audit logging, supply-chain controls, and real-environment smoke testing.

## External Guidance Reviewed

- OWASP GenAI Security Project, Top 10 for LLM Applications, especially prompt injection, sensitive information disclosure, insecure output handling, excessive agency, and supply-chain risks: https://owasp.org/www-project-top-10-for-large-language-model-applications/
- GitHub Actions secure-use reference for least-privilege `GITHUB_TOKEN`, SHA-pinned actions, and secret handling: https://docs.github.com/en/actions/reference/security/secure-use
- GitHub dependency review and Dependabot guidance for blocking vulnerable dependency changes: https://docs.github.com/en/code-security/concepts/supply-chain-security/about-dependency-review
- PyPI trusted publishing documentation for OIDC-based package publishing: https://docs.pypi.org/trusted-publishers/
- PyPA `pip-audit` for Python dependency vulnerability checks: https://github.com/pypa/pip-audit
- OpenSSF Scorecard for supply-chain health checks: https://scorecard.dev/

## Mitigated Findings

### S1. Agent subprocess approval and sandbox defaults

**Status:** Mitigated in the local working tree.

Evidence:

- [sub_agents.py](../../packages/core/src/autogenesis_core/sub_agents.py) now defaults Codex subprocesses to `approval_policy="on-request"` and `sandbox_mode="workspace-write"`.
- [client.py](../../packages/tui/src/autogenesis_tui/client.py) now starts TUI threads with approval policy `on-request`.
- [server.py](../../packages/tui/src/autogenesis_tui/server.py) now starts `codex app-server` with approval policy `on-request` and workspace-write sandbox.

GitNexus still marks `SubAgentManager.spawn` as CRITICAL blast radius because it directly affects employee dispatch and CEO orchestration. That blast radius is expected; the default policy is now safer, and unsafe bypass requires explicit opt-in.

Residual work:

- Add end-to-end approval-gating tests against real Codex CLI behavior.
- Persist approval decisions and subprocess policy choices to the audit trail.

### S2. Shell and filesystem tool boundaries

**Status:** Mitigated in the local working tree.

Evidence:

- [sandbox.py](../../packages/security/src/autogenesis_security/sandbox.py) now defines `WorkspacePolicy`, `CommandPolicy`, and argv-based `SubprocessSandbox` execution.
- [bash.py](../../packages/tools/src/autogenesis_tools/bash.py) now routes through `SubprocessSandbox` with a default allowed-command set.
- [filesystem.py](../../packages/tools/src/autogenesis_tools/filesystem.py) now resolves read/write/edit/glob/grep/list paths through `WorkspacePolicy`.

Residual work:

- Add universal audit events for every command/path decision.
- Consider an OS/container sandbox provider for stronger isolation than local subprocess policy.

### S3. Twitter gateway/poster contract and auth

**Status:** Mitigated in the local working tree.

Evidence:

- [gateway.py](../../packages/twitter/src/autogenesis_twitter/gateway.py) now requires a non-empty gateway token unless explicit test mode is enabled.
- The gateway now implements `/twitter/status`, request-size limits, JSON parse errors, tweet-length checks, and aligned `id`/`tweet_id` response fields.
- [poster.py](../../packages/twitter/src/autogenesis_twitter/poster.py) accepts both `id` and `tweet_id`.

Residual work:

- Run a real Twitter API smoke test in a controlled environment before trusting public posting.
- Add request/action audit events for gateway posting attempts.

## Active Findings

### S4. Prompt-injection and output guardrails exist but do not protect the main agent loop

Evidence:

- [guardrails.py](../../packages/security/src/autogenesis_security/guardrails.py#L53) defines input checks.
- [scanner.py](../../packages/security/src/autogenesis_security/scanner.py#L31) runs adversarial prompt checks.
- The CEO and employee dispatch paths do not enforce these guardrails before tool execution.

Recommended work:

- Integrate guardrails at task intake, tool-call approval, external-content ingestion, and output-to-public-action boundaries.
- Map tests to OWASP LLM risks: prompt injection, sensitive data disclosure, excessive agency, insecure output handling, and supply-chain compromise.

### S5. OAuth/JWT handling decodes claims without verification

Evidence:

- [auth.py](../../packages/core/src/autogenesis_core/auth.py#L93) decodes JWTs with signature and expiration verification disabled.
- [auth.py](../../packages/core/src/autogenesis_core/auth.py#L80) uses decoded token `exp` to decide whether the token is expiring.

This is acceptable only for local UX hints, never for authorization. Document this boundary and avoid trusting unverified claims for access control.

### S6. CI and release security are partially strong but incomplete

Evidence:

- Actions are pinned to full commit SHAs and default workflow permissions are mostly read-only.
- [release.yml](../../.github/workflows/release.yml#L60) uses PyPI trusted publishing.
- No Dependabot config, dependency review workflow, CodeQL, OpenSSF Scorecard, secret scanning policy, or artifact attestation workflow is present.

Recommended work:

- Add Dependabot version/security updates for `uv` and GitHub Actions.
- Add dependency review on PRs.
- Add OpenSSF Scorecard on a schedule.
- Add CodeQL or equivalent Python static analysis.
- Consider artifact attestations for release artifacts.

### S7. Audit logging exists but is not a universal security trail

Evidence:

- [audit.py](../../packages/security/src/autogenesis_security/audit.py#L41) appends JSONL audit events.
- Tool execution, approval decisions, gateway requests, and employee dispatch do not consistently emit audit events.

Recommended work:

- Record who/what initiated each tool call, policy decision, command, target path, public-posting action, and result.
- Redact secrets before writing audit logs.

## Verification Commands

```bash
uv sync --all-extras
uv run pytest packages/*/tests tests -q --tb=short
uv run pytest packages/*/tests/ -q --tb=short --cov --cov-report=term-missing --cov-fail-under=80
uv run ruff check --select S packages/
uvx pip-audit
uv build --all-packages --out-dir /tmp/autogenesis-dist
```

Results from this audit:

- Tests: 457 passed on Python 3.13.12.
- Coverage: 86.65% total coverage on Python 3.13.12.
- Full Ruff lint: passed.
- Strict mypy: passed.
- Security lint: passed.
- Dependency audit: no known vulnerabilities found.
- Build: all packages built successfully.

## Security Roadmap

1. Wire guardrails and audit logging into actual execution paths.
2. Add live-smoke tests for Codex app-server approval policy and Twitter gateway posting.
3. Add supply-chain controls in GitHub: Dependabot, dependency review, CodeQL, OpenSSF Scorecard, and release attestations.
4. Strengthen local subprocess isolation with an OS/container sandbox provider if autonomous tool use expands.
