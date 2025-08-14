# Azure Services Setup Guide

## Required Azure Resources

### 1. Azure Cosmos DB
```bash
# Create resource group
az group create --name snippy-ai-rg --location eastus

# Create Cosmos DB account with vector search capabilities
az cosmosdb create \
  --name snippy-cosmos-$(date +%s) \
  --resource-group snippy-ai-rg \
  --kind GlobalDocumentDB \
  --locations regionName=eastus \
  --capabilities EnableServerless EnableNoSQLVectorSearch

# Get connection string
az cosmosdb keys list --name <cosmos-account-name> --resource-group snippy-ai-rg --type connection-strings
```

### 2. Azure OpenAI
```bash
# Create Azure OpenAI resource
az cognitiveservices account create \
  --name snippy-openai-$(date +%s) \
  --resource-group snippy-ai-rg \
  --kind OpenAI \
  --sku S0 \
  --location eastus

# Deploy embedding model
az cognitiveservices account deployment create \
  --name <openai-account-name> \
  --resource-group snippy-ai-rg \
  --deployment-name text-embedding-3-small \
  --model-name text-embedding-3-small \
  --model-version "1" \
  --model-format OpenAI \
  --scale-settings-scale-type Standard

# Deploy chat model  
az cognitiveservices account deployment create \
  --name <openai-account-name> \
  --resource-group snippy-ai-rg \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-05-13" \
  --model-format OpenAI \
  --scale-settings-scale-type Standard
```

### 3. Azure AI Project
```bash
# Create AI Hub
az ml workspace create \
  --name snippy-ai-hub \
  --resource-group snippy-ai-rg \
  --location eastus \
  --kind hub

# Create AI Project
az ml workspace create \
  --name snippy-ai-project \
  --resource-group snippy-ai-rg \
  --location eastus \
  --kind project \
  --hub-id /subscriptions/<subscription-id>/resourceGroups/snippy-ai-rg/providers/Microsoft.MachineLearningServices/workspaces/snippy-ai-hub
```

### 4. Storage Account
```bash
# Create storage account
az storage account create \
  --name snippystorage$(date +%s) \
  --resource-group snippy-ai-rg \
  --location eastus \
  --sku Standard_LRS
```

## Update Configuration

After creating resources, update `local.settings.json` with:

1. **COSMOS_ENDPOINT**: From Cosmos DB connection string
2. **PROJECT_CONNECTION_STRING**: From AI Project 
3. **AZURE_OPENAI_ENDPOINT**: From OpenAI resource
4. **AZURE_OPENAI_KEY**: From OpenAI resource keys

## Test Connection

Set `DISABLE_OPENAI=0` and restart the function app to test real Azure services.
