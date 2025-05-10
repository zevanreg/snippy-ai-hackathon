#!/usr/bin/env bash
set -e

# Move into the repo’s src folder and activate the virtual‑env if present
cd /workspaces/$(basename "$GITHUB_REPOSITORY")/src
if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
fi

# ── Cosmos DB Linux emulator ──────────────────────────────────────────────
# Runs in gateway mode so localhost:8081 works with the default connection string
if ! docker ps --filter "name=cosmos-emu" --format '{{.Names}}' | grep -q cosmos-emu; then
  echo "▶ Starting Cosmos DB emulator container"
  docker run -d --name cosmos-emu \
    -p 8081:8081 -p 8900:8900 \
    mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator
fi

# ── Azurite storage emulator (blob / queue / table) ───────────────────────
# Needed because local.settings.json uses UseDevelopmentStorage=true
if ! pgrep -f "azurite.*--location" >/dev/null; then
  echo "▶ Starting Azurite storage emulator"
  AZURITE_DATA_DIR=/workspaces/.azurite
  mkdir -p "$AZURITE_DATA_DIR"
  nohup azurite --silent \
        --location "$AZURITE_DATA_DIR" \
        --blobHost 0.0.0.0 --queueHost 0.0.0.0 --tableHost 0.0.0.0 &
fi

# ── Azure Functions runtime ───────────────────────────────────────────────
echo "▶ func start (port 7071)"
func start --python --no-build
