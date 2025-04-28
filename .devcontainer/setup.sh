#!/usr/bin/env bash
set -e

echo "▶ Installing Python deps with uv"
pip install -q 'uv>=0.1.29'
cd /workspaces/$(basename "$GITHUB_REPOSITORY")/src
uv venv .venv
uv pip install -r requirements.txt

echo "▶ Creating local.settings.json from Codespaces secrets"
jq -n '{
  IsEncrypted:false,
  Values:{
    AzureWebJobsStorage      : env.AzureWebJobsStorage,
    AzureWebJobsFeatureFlags : "EnableWorkerIndexing",
    FUNCTIONS_WORKER_RUNTIME : "python",
    COSMOS_CONN              : env.COSMOS_CONN,
    COSMOS_DATABASE_NAME     : "dev-snippet-db",
    COSMOS_CONTAINER_NAME    : "code-snippets",
    BLOB_CONTAINER_NAME      : "snippet-backups",
    EMBEDDING_MODEL_DEPLOYMENT_NAME : "text-embedding-3-small",
    AGENTS_MODEL_DEPLOYMENT_NAME    : "gpt-4o",
    PROJECT_CONNECTION_STRING       : env.PROJECT_CONNECTION_STRING,
    PYTHON_ENABLE_WORKER_EXTENSIONS : "True",
    AZURE_OPENAI_ENDPOINT           : env.AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_KEY                : env.AZURE_OPENAI_KEY,
    COSMOS_VECTOR_TOP_K             : "30"
  }
}' > local.settings.json 