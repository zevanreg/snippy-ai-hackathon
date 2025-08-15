#!/bin/bash

# Get values from azd environment
echo "Getting environment values from azd..."
COSMOS_ENDPOINT=$(azd env get-values | grep COSMOS_ENDPOINT | cut -d'"' -f2)
COSMOS_KEY=$(azd env get-values | grep COSMOS_KEY | cut -d'"' -f2)
COSMOS_DATABASE_NAME=$(azd env get-values | grep COSMOS_DATABASE_NAME | cut -d'"' -f2)
COSMOS_CONTAINER_NAME=$(azd env get-values | grep COSMOS_CONTAINER_NAME | cut -d'"' -f2)
AI_PROJECT_CONNECTION_STRING=$(azd env get-values | grep AI_PROJECT_CONNECTION_STRING | cut -d'"' -f2)
AI_FOUNDRY_OPENAI_ENDPOINT=$(azd env get-values | grep AI_FOUNDRY_OPENAI_ENDPOINT | cut -d'"' -f2)
AI_FOUNDRY_OPENAI_KEY=$(azd env get-values | grep AI_FOUNDRY_OPENAI_KEY | cut -d'"' -f2)
STORAGE_CONNECTION_STRING=$(azd env get-values | grep STORAGE_CONNECTION_STRING | cut -d'"' -f2)
STORAGE_CONTAINER_SNIPPETBACKUPS=$(azd env get-values | grep STORAGE_CONTAINER_SNIPPETBACKUPS | cut -d'"' -f2)
STORAGE_CONTAINER_SNIPPETINPUT=$(azd env get-values | grep STORAGE_CONTAINER_SNIPPETINPUT | cut -d'"' -f2)
EMBEDDING_MODEL_DEPLOYMENT_NAME=$(azd env get-values | grep EMBEDDING_MODEL_DEPLOYMENT_NAME | cut -d'"' -f2)
CHAT_MODEL_DEPLOYMENT_NAME=$(azd env get-values | grep CHAT_MODEL_DEPLOYMENT_NAME | cut -d'"' -f2)
APP_INSIGHTS_CONNECTION_STRING=$(azd env get-values | grep APP_INSIGHTS_CONNECTION_STRING | cut -d'"' -f2)

# Create or update local.settings.json
echo "Generating local.settings.json in src directory..."
cat > src/local.settings.json << EOF
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "${STORAGE_CONNECTION_STRING:-UseDevelopmentStorage=true}",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "PYTHON_ENABLE_WORKER_EXTENSIONS": "True",
    "COSMOS_DATABASE_NAME": "${COSMOS_DATABASE_NAME:-dev-snippet-db}",
    "COSMOS_CONTAINER_NAME": "${COSMOS_CONTAINER_NAME:-code-snippets}",
    "COSMOS_VECTOR_TOP_K": "30",
    "BLOB_CONTAINER_NAME": "${STORAGE_CONTAINER_SNIPPETBACKUPS:-snippet-backups}",
    "EMBEDDING_MODEL_DEPLOYMENT_NAME": "${EMBEDDING_MODEL_DEPLOYMENT_NAME:-text-embedding-3-small}",
    "AGENTS_MODEL_DEPLOYMENT_NAME": "${CHAT_MODEL_DEPLOYMENT_NAME:-gpt-4o}",
    "COSMOS_ENDPOINT": "${COSMOS_ENDPOINT:-https://localhost:8081}",
    "COSMOS_KEY": "${COSMOS_KEY:-}",
    "PROJECT_CONNECTION_STRING": "${AI_PROJECT_CONNECTION_STRING:-}",
    "AZURE_OPENAI_ENDPOINT": "${AI_FOUNDRY_OPENAI_ENDPOINT:-}",
    "AZURE_OPENAI_KEY": "${AI_FOUNDRY_OPENAI_KEY:-}",
    "VECTOR_TOP_K": "5",
    "OPENAI_TEMPERATURE": "0.2",
    "REQUEST_TIMEOUT_SEC": "20",
    "CHUNK_SIZE": "800",
    "DISABLE_OPENAI": "0",
    "INGESTION_CONTAINER": "${STORAGE_CONTAINER_SNIPPETINPUT:-snippet-input}",
    "MAX_BLOB_MB": "2",
    "DEFAULT_PROJECT_ID": "default-project",
    "OPENAI_CHAT_MODEL": "${CHAT_MODEL_DEPLOYMENT_NAME:-gpt-4o}",
    "MAX_AGENT_ITERATIONS": "3",
    "AGENT_TOKEN_LIMIT": "4000",
    "ENABLE_CONTENT_FILTER": "0",
    "MAX_CONCURRENT_AGENTS": "3",
    "APPLICATIONINSIGHTS_CONNECTION_STRING": "${APP_INSIGHTS_CONNECTION_STRING:-}"
  }
}
EOF

echo "local.settings.json generated successfully in src directory!"
echo "Using Cosmos DB: ${COSMOS_ENDPOINT}"
echo "Using AI Foundry: ${AI_FOUNDRY_OPENAI_ENDPOINT}"
echo "Using Storage: ${STORAGE_CONNECTION_STRING%%AccountKey=*}AccountKey=***"