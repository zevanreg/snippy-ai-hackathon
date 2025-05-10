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

# ── Cosmos DB Linux emulator ──────────────────────────────────────────────
# Runs in gateway mode so the default connection string against localhost works.
if ! docker ps --filter "name=cosmos-emu" --format '{{.Names}}' | grep -q cosmos-emu; then
  echo "▶ Starting Cosmos DB emulator container"
  docker run -d --name cosmos-emu \
    -p 8081:8081 -p 8900:8900 \
    mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator
fi

# ── Azurite storage emulator (blob / queue / table) ───────────────────────
if ! pgrep -f "azurite.*--location" >/dev/null; then
  echo "▶ Starting Azurite storage emulator"
  AZURITE_DATA_DIR="$REPO_ROOT/.azurite"
  mkdir -p "$AZURITE_DATA_DIR"
  nohup azurite --silent \
        --location "$AZURITE_DATA_DIR" \
        --blobHost 0.0.0.0 --queueHost 0.0.0.0 --tableHost 0.0.0.0 \
        > "$AZURITE_DATA_DIR/azurite.log" 2>&1 &
fi

# The Functions host needs a storage connection string even when using Azurite.
export AzureWebJobsStorage="UseDevelopmentStorage=true"

# ── Azure Functions runtime ───────────────────────────────────────────────
echo "▶ func start (port 7071)"
func start --python --no-build --port 7071
