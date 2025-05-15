#!/usr/bin/env bash
set -euo pipefail

# ── Paths ────────────────────────────────────────────────────────────────
REPO_ROOT="/workspaces/$(basename "$GITHUB_REPOSITORY")"
SRC_DIR="$REPO_ROOT/src"

cd "$SRC_DIR"

# ── Python virtual environment ────────────────────────────────────────────
if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
fi

# ── Azure Functions runtime ───────────────────────────────────────────────
echo "▶ func start (port 7071)"
func start --python --no-build --port 7071
