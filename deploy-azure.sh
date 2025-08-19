#!/bin/bash

# Azure Functions Deployment Script
# This script deploys the function app to Azure

set -e

# Configuration
RESOURCE_GROUP="snippy-ai-rg"
FUNCTION_APP_NAME="snippy-functions-$(date +%s)"
STORAGE_ACCOUNT="snippystore$(date +%s)"
LOCATION="eastus"
PYTHON_VERSION="3.11"

echo "🚀 Starting Azure Functions deployment..."

# 1. Create Resource Group
echo "📦 Creating resource group..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION

# 2. Create Storage Account
echo "💾 Creating storage account..."
az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS \
    --kind StorageV2

# 3. Create Function App
echo "⚡ Creating Function App..."
az functionapp create \
    --name $FUNCTION_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --storage-account $STORAGE_ACCOUNT \
    --consumption-plan-location $LOCATION \
    --runtime python \
    --runtime-version $PYTHON_VERSION \
    --functions-version 4 \
    --os-type Linux

# 4. Configure Application Settings
echo "⚙️  Configuring application settings..."

# Copy application settings from local.settings.json
az functionapp config appsettings set \
    --name $FUNCTION_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
        FUNCTIONS_WORKER_RUNTIME=python \
        PYTHON_ENABLE_WORKER_EXTENSIONS=True \
        COSMOS_DATABASE_NAME="prod-snippet-db" \
        COSMOS_CONTAINER_NAME="code-snippets" \
        COSMOS_VECTOR_TOP_K=30 \
        BLOB_CONTAINER_NAME="snippet-backups" \
        EMBEDDING_MODEL_DEPLOYMENT_NAME="text-embedding-3-small" \
        AGENTS_MODEL_DEPLOYMENT_NAME="gpt-4o" \
        VECTOR_TOP_K=5 \
        OPENAI_TEMPERATURE=0.2 \
        REQUEST_TIMEOUT_SEC=20 \
        CHUNK_SIZE=800 \
        INGESTION_CONTAINER="snippet-input" \
        MAX_BLOB_MB=2 \
        DEFAULT_PROJECT_ID="default-project" \
        OPENAI_CHAT_MODEL="gpt-4o" \
        MAX_AGENT_ITERATIONS=3 \
        AGENT_TOKEN_LIMIT=4000 \
        ENABLE_CONTENT_FILTER=1 \
        MAX_CONCURRENT_AGENTS=3

# 5. Deploy Function Code
echo "📤 Deploying function code..."
cd /workspaces/snippy-ai-hackathon/src
func azure functionapp publish $FUNCTION_APP_NAME --python

echo "✅ Deployment completed!"
echo "🌐 Function App URL: https://$FUNCTION_APP_NAME.azurewebsites.net"
echo "📊 Monitor at: https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$FUNCTION_APP_NAME"

# 6. Test deployment
echo "🧪 Testing deployment..."
sleep 30  # Wait for deployment to settle

echo "Testing health endpoint..."
curl -f "https://$FUNCTION_APP_NAME.azurewebsites.net/api/snippets" || echo "❌ Health check failed"

echo "🎉 Deployment script completed!"
echo "📝 Next steps:"
echo "   1. Configure Azure service connection strings in the portal"
echo "   2. Test all endpoints"
echo "   3. Set up monitoring and alerts"
