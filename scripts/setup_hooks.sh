#!/usr/bin/env bash
# ==============================================================================
# Setup Git Hooks for DiligentEdu
# Run this script once after cloning to activate pre-commit linter hooks:
#   bash scripts/setup_hooks.sh
# ==============================================================================

set -e

# Change to repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=========================================="
echo "🚀 Setting up Git Hooks for DiligentEdu"
echo "=========================================="

# 1. Ensure hooks directory permissions
if [ -f ".githooks/pre-commit" ]; then
    chmod +x .githooks/pre-commit
    echo "✓ Set executable permissions on .githooks/pre-commit"
fi

# 2. Configure Git to use version-controlled .githooks directory
git config core.hooksPath .githooks
echo "✓ Configured git core.hooksPath -> .githooks"

# 3. If uv or pre-commit is available, install dev dependencies
if command -v uv &> /dev/null; then
    echo "✓ Detected 'uv'. Installing dev dependencies..."
    uv sync --group dev
    echo "✓ Dev dependencies synced."
fi

echo "=========================================="
echo "🎉 Git hooks setup complete!"
echo "Linters will now run automatically on every 'git commit'."
echo "To run checks manually at any time:"
echo "  uv run pre-commit run --all-files"
echo "  # or"
echo "  uv run ruff check . && uv run ruff format --check ."
echo "=========================================="
