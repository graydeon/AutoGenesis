# Contributing to AutoGenesis

Thank you for your interest in contributing to AutoGenesis!

## Quick Start

```bash
git clone https://github.com/graydeon/AutoGenesis.git
cd AutoGenesis
./scripts/dev-setup.sh
```

This installs Python dependencies, sets up pre-commit hooks, and verifies your environment. Requires Python 3.11+.

## Development Workflow

### Branch Naming

- `feat/description` — new features
- `fix/description` — bug fixes
- `docs/description` — documentation changes
- `security/description` — security improvements

### Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(core): add context compression to agent loop
fix(tokens): correct budget calculation for cached responses
docs: update getting-started guide
security(guardrails): add new prompt injection pattern
```

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with tests
3. Ensure all checks pass: `uv run ruff check . && uv run mypy packages/ && uv run pytest`
4. Submit a PR using the PR template
5. Address review feedback

## Code Style

- **Formatter:** `ruff format`
- **Linter:** `ruff check` (with `--select ALL`)
- **Type checker:** `mypy` in strict mode
- **Type hints:** Required on all public functions
- **Data models:** Use Pydantic V2 for all structured data
- **Imports:** Absolute imports only
- **Docstrings:** Google style on all public APIs
- **File size:** No file > 500 lines; split if approaching
- **Function size:** No function > 50 lines; extract helpers

## Testing

- Framework: pytest with pytest-asyncio
- Style: Use fixtures and `pytest.mark.parametrize`, not `unittest.TestCase`
- Coverage: 80% minimum for new code
- Run tests: `uv run pytest -v --cov`
- Run specific package: `uv run pytest packages/core/tests/ -v`

## Prompt Contributions

Prompts in `prompts/` are versioned artifacts. When modifying prompts:

1. Never edit `prompts/system/constitution.yaml` — constitutional rules are immutable
2. Bump the version in the prompt file header
3. Update `prompts/manifest.yaml` with the new version
4. Add golden tests in `prompts/tests/` to prevent regression
5. Run `autogenesis optimize check` to verify no drift

## Reporting Security Vulnerabilities

Please report security vulnerabilities responsibly. See [SECURITY.md](SECURITY.md) for our disclosure process. Do not open public issues for security vulnerabilities.

## Good First Issues

Look for issues labeled `good first issue` on our [issue tracker](https://github.com/graydeon/AutoGenesis/issues).
