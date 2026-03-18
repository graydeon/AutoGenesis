# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1](https://github.com/graydeon/AutoGenesis/compare/autogenesis-v0.1.0...autogenesis-v0.1.1) (2026-03-18)


### Features

* Add CI/CD pipeline with GitHub Actions workflows and templates ([abb1610](https://github.com/graydeon/AutoGenesis/commit/abb1610c94193e68e5cccc950b5bf439f6224499))
* Add developer tooling with dev-setup script and pre-commit hooks ([856ffb3](https://github.com/graydeon/AutoGenesis/commit/856ffb368ca17c1fba4b6a2084eb53c5e2d47483))
* **cli:** Implement chat, run, init, and config commands with Rich display ([cb92129](https://github.com/graydeon/AutoGenesis/commit/cb92129abad6f4367371067cd3689da700da93d7))
* **core:** Implement Phase 2 core runtime — router, events, loop, state, context ([f59296f](https://github.com/graydeon/AutoGenesis/commit/f59296fa25e27d2ad92ecd4c2a5261d2f8e82560))
* **core:** Implement Pydantic data models and XDG config system ([b4337bd](https://github.com/graydeon/AutoGenesis/commit/b4337bda010e114825ce118a896f89d00c854f91))
* **mcp:** Implement MCP client, server, and registry with allowlisting ([66d4b51](https://github.com/graydeon/AutoGenesis/commit/66d4b51b2ef40ac5036615060de48da05cad8b2c))
* **optimizer:** Implement self-improving prompt engine with constitutional safety ([e8d5044](https://github.com/graydeon/AutoGenesis/commit/e8d5044f229faa244c5b78e22c24f9da34e29205))
* **plugins:** Implement plugin interface, manifest validation, and loader ([3301eaf](https://github.com/graydeon/AutoGenesis/commit/3301eafe777034d050d276d2324fbcb8788135c9))
* Scaffold monorepo skeleton with 8 uv workspace packages ([6f535c9](https://github.com/graydeon/AutoGenesis/commit/6f535c9be2f32a02cbb3b08d24f52eda4d68745d))
* **security:** Implement guardrails, allowlisting, audit logging, scanner, and sandbox ([3976371](https://github.com/graydeon/AutoGenesis/commit/3976371d2d6e476c05cd994b5fc0558bfb47fd99))
* **tokens:** Implement token counting, budgeting, caching, compression, and reporting ([8ae481b](https://github.com/graydeon/AutoGenesis/commit/8ae481bd37d10b25b9f587e7237619c038b51c72))
* **tools:** Implement tool registry with progressive disclosure and 12 built-in tools ([382b88b](https://github.com/graydeon/AutoGenesis/commit/382b88b9a9ba3dafbccca04e75f5ce5964ca1bfc))


### Bug Fixes

* Add missing __version__ to all package __init__.py files ([a96f537](https://github.com/graydeon/AutoGenesis/commit/a96f537e2ac0cb0143fd9a16ba99268641ff75e2))
* **ci:** Fix build check, security check, and format issues ([d558272](https://github.com/graydeon/AutoGenesis/commit/d5582721df806ac6b70be5e71452f11b0ee83dcd))


### Documentation

* Add AutoGenesis v0.1.0 design specification ([e653056](https://github.com/graydeon/AutoGenesis/commit/e65305674f9756d412029623906c000fa9d7315d))
* Add AutoGenesis v0.1.0 implementation plan ([f4dcbf4](https://github.com/graydeon/AutoGenesis/commit/f4dcbf492a643d24369d853a5b71edb4ded8f833))
* Add community, governance, and legal files ([71335ff](https://github.com/graydeon/AutoGenesis/commit/71335ff3d7a0bbda97dc2454ee5297df9bd3f99a))

## [Unreleased]

### Added

- Monorepo skeleton with 8 uv workspace packages: core, cli, tools, mcp, tokens, optimizer, security, plugins.
- CLI scaffolding with Typer + Rich: `init`, `chat`, `run`, `config`, `tokens`, `optimize`, `scan`, `audit`, `mcp`, `plugins` commands.
- Project governance, contributing guidelines, and community files.
