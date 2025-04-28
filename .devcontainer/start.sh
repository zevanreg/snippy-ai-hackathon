#!/usr/bin/env bash
set -e
cd /workspaces/$(basename "$GITHUB_REPOSITORY")/src
source .venv/bin/activate

# Start Cosmos DB Linux emulator (gateway mode) in the background so
# your original connection string still works if you point it at localhost.
# Comment this block out if you prefer a real Cosmos account.
if ! docker ps --filter "name=cosmos-emu" --format '{{.Names}}' | grep -q cosmos-emu; then
  echo "▶ Starting Cosmos DB emulator container"
  docker run -d --name cosmos-emu \
    -p 8081:8081 -p 8900:8900 \
    mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator
fi

# Start the Functions runtime
echo "▶ func start (port 7071)"
func start --python --no-build 