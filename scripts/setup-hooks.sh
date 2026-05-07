#!/bin/bash
# Install pre-commit hooks for Vectaris
#
# Usage: ./scripts/setup-hooks.sh

set -e

echo "📦 Installing pre-commit..."
pip install pre-commit

echo "🔧 Installing git hooks..."
pre-commit install

echo "✅ Pre-commit hooks installed successfully!"
echo ""
echo "To run hooks manually:"
echo "  pre-commit run --all-files"
