# Security Policy

AutoGenesis takes security seriously. The framework includes built-in security features (guardrails, audit logging, adversarial self-scanning), and we hold our own codebase to the same standard.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.x.x   | :white_check_mark: |

Once v1.0.0 is released, only the latest minor release will receive security patches.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, please report vulnerabilities through one of these channels:

1. **Email:** [security@autogenesis.dev](mailto:security@autogenesis.dev)
2. **GitHub Private Advisory:** Use [GitHub's Security Advisory feature](https://github.com/graydeon/AutoGenesis/security/advisories/new) to submit a private report.

### What to Include

- A clear description of the vulnerability and its potential impact.
- Steps to reproduce or a proof-of-concept.
- The version(s) affected.
- Any suggested remediation, if you have one.

### Our Commitment

- **Acknowledgment:** We will acknowledge receipt of your report within **48 hours**.
- **Triage:** We will provide an initial assessment within **7 days**.
- **Resolution:** We aim to release a fix within **30 days** of confirming the vulnerability.
- **Disclosure:** We follow a **90-day coordinated disclosure timeline**. If a fix is released sooner, we will coordinate public disclosure with you at that point. If 90 days pass without a fix, you are free to disclose publicly.

### Credit

We are happy to credit reporters in release notes and the CHANGELOG unless you prefer to remain anonymous. Let us know your preference when reporting.

## Security-Related Features

AutoGenesis includes several built-in security mechanisms:

- **Guardrails:** Configurable constraints on agent actions (file system access, network calls, shell commands).
- **Audit Logging:** Every agent action and tool invocation is logged with full context for post-hoc review.
- **Self-Pentesting:** The `autogenesis scan` command runs adversarial probes against your agent configuration to surface prompt injection risks and guardrail bypasses.
- **Token Budgets:** Hard limits on token spend per session prevent runaway costs from compromised or misbehaving agents.

If you discover a bypass for any of these mechanisms, that qualifies as a security vulnerability — please report it through the channels above.

## Scope

The following are **in scope** for security reports:

- Prompt injection vulnerabilities in the agent loop.
- Guardrail bypasses that allow unauthorized tool execution.
- Audit log tampering or evasion.
- Credential or secret leakage through logs, caches, or error messages.
- Dependency vulnerabilities that are exploitable in AutoGenesis's usage context.
- Plugin sandbox escapes.

The following are **out of scope**:

- Vulnerabilities in upstream LLM providers (report those to the provider directly).
- Denial-of-service via excessive API calls (mitigated by token budgets, but not a security boundary).
- Social engineering attacks that require tricking a user into running malicious commands.
