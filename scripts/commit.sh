#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 \"commit message\"" >&2
  exit 1
fi

COMMIT_MSG="$1"

echo "Running test suite before committing..."
poetry run pytest --cov=src --cov-report=term

echo "Staging changes..."
git add -A

if git diff --cached --quiet; then
  echo "No changes staged for commit. Aborting."
  exit 1
fi

echo "Creating commit..."
git commit -m "${COMMIT_MSG}"

echo "Commit created successfully."
