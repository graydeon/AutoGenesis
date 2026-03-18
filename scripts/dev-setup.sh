#!/usr/bin/env bash
set -euo pipefail

echo "=== AutoGenesis Dev Setup ==="

# Check Python 3.11+
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required="3.11"
if [ "$(printf '%s\n' "$required" "$python_version" | sort -V | head -n1)" != "$required" ]; then
    echo "ERROR: Python 3.11+ required (found $python_version)"
    exit 1
fi

# Check/install uv
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Sync workspace
echo "Syncing workspace..."
uv sync --all-extras

# Install pre-commit hooks
if command -v pre-commit &>/dev/null || uv run pre-commit --version &>/dev/null 2>&1; then
    echo "Installing pre-commit hooks..."
    uv run pre-commit install
fi

echo ""
echo "=== Setup complete! ==="
echo "Next steps:"
echo "  uv run pytest              # run tests"
echo "  uv run autogenesis --help  # CLI"
echo "  uv run ruff check .       # lint"
