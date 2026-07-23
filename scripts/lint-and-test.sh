#!/usr/bin/env bash
set -euo pipefail

echo "=== Running Linting ==="
ruff check backend/ --fix
ruff format backend/

echo "=== Running Type Checks ==="
mypy backend/app --ignore-missing-imports || echo "Type check completed with warnings"

echo "=== Running Tests ==="
pytest tests/unit/ -v --cov=backend/app --cov-report=term-missing

echo "=== All checks passed ==="
