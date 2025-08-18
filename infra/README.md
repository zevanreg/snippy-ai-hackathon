# Hackathon Infrastructure Deployment Guide

## Progressive Level-Based Deployment

This hackathon uses a **progressive deployment approach** where attendees can deploy infrastructure incrementally as they advance through levels 1-6. Each level builds upon the previous one, adding new capabilities and resources.

## Deployment Approach

**Progressive Infrastructure Deployment**: Resources are deployed progressively by level, allowing attendees to:
- ✅ Deploy only what they need for their current level
- ✅ Understand infrastructure complexity incrementally  
- ✅ Save costs by not deploying unused resources
- ✅ Focus on level-specific challenges without infrastructure overhead

## Deployment Levels

### Level 1: Foundation (Basic HTTP API)
Deploy basic infrastructure with Cosmos DB and Function App (no AI services)

```bash
az deployment sub create \
  --location eastus \
  --template-file levels/level-1/main.bicep \
  --parameters environmentName=your-env-name location=eastus
```

**Resources deployed:**
- Function App (Consumption plan)
- Cosmos DB (Basic configuration, no vector search)
- Storage Account (for Function App runtime)

**Available endpoints:**
- `/api/health` - Health check
- `/api/snippets` - CRUD operations for code snippets

### Level 2: AI Services (Embeddings)
Add Azure AI Foundry and embedding capabilities

```bash
az deployment sub create \
  --location eastus \
  --template-file levels/level-2/main.bicep \
  --parameters environmentName=your-env-name location=eastus
```

**New resources added:**
- Azure AI Foundry (OpenAI services)
- Embedding model deployment (text-embedding-3-small)
- Application Insights (monitoring)
- Cosmos DB enhanced with vector search capability

**New endpoints:**
- `/api/orchestrators/embeddings` - Generate and store embeddings

### Level 3: Chat Completion
Add conversational AI capabilities

```bash
az deployment sub create \
  --location eastus \
  --template-file levels/level-3/main.bicep \
  --parameters environmentName=your-env-name location=eastus
```

**New resources added:**
- Chat model deployment (GPT-4o)

**New endpoints:**
- `/api/query` - Vector search with chat completions

### Level 4: Blob Storage & Monitoring
Add file ingestion and enhanced monitoring

```bash
az deployment sub create \
  --location eastus \
  --template-file levels/level-4/main.bicep \
  --parameters environmentName=your-env-name location=eastus
```

**New resources added:**
- Blob containers (snippet-inputs, snippet-backups)
- Enhanced storage permissions

**New endpoints:**
- `/api/orchestrators/ingestion` - Blob-triggered processing

### Level 5: Multi-agent Orchestration
Enable complex AI workflows

```bash
az deployment sub create \
  --location eastus \
  --template-file levels/level-5/main.bicep \
  --parameters environmentName=your-env-name location=eastus
```

**New capabilities:**
- Enhanced Durable Functions configuration
- Multi-agent orchestration patterns

**New endpoints:**
- `/api/orchestrators/multi-agent` - Complex AI workflows

### Level 6: Zero Trust Security
Add enterprise-grade security

```bash
az deployment sub create \
  --location eastus \
  --template-file levels/level-6/main.bicep \
  --parameters environmentName=your-env-name location=eastus
```

**New resources added:**
- Azure Key Vault
- Enhanced RBAC and security configuration

**Security enhancements:**
- Credential storage in Key Vault
- Zero trust security patterns
- Enhanced authentication and authorization

## Quick Start Commands

### Prerequisites
```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "your-subscription-id"
```

### Deploy for Your Target Level

**Choose your target level and deploy:**

```bash
# For Level 1 (Foundation)
az deployment sub create \
  --location eastus \
  --template-file infra/level-1.bicep \
  --parameters environmentName=dev location=eastus

# For Level 3 (includes Levels 1, 2, and 3)
az deployment sub create \
  --location eastus \
  --template-file levels/level-3/main.bicep \
  --parameters environmentName=dev location=eastus

# For Level 6 (Complete platform)
az deployment sub create \
  --location eastus \
  --template-file levels/level-6/main.bicep \
  --parameters environmentName=dev location=eastus
```

## Architecture Overview

```
Level 1: Function App + Cosmos DB (Basic)
    ↓
Level 2: + AI Foundry + Embeddings + App Insights  
    ↓
Level 3: + Chat Model (GPT-4o)
    ↓
Level 4: + Blob Storage + Enhanced Monitoring
    ↓
Level 5: + Multi-agent Orchestration
    ↓
Level 6: + Key Vault + Zero Trust Security
```

**Infrastructure Files:**
- `levels/level-X/main.bicep` - Progressive deployment templates (X = 1-6)
- `levels/level-X/resources.bicep` - Modular resource definitions per level
- `levels/level-X/README.md` - Level-specific documentation
- `README.md` - This deployment guide

**Note:** Legacy `main.bicep` and `hackathon-resources.bicep` have been replaced by the progressive level-based approach for better learning experience and cost optimization.

## Resource Naming Convention

All resources use a consistent naming pattern with the resource token:
- Resource Group: `rg-snippy-hackathon-{environmentName}`
- Function App: `func-{resourceToken}`
- Cosmos DB: `cosmos-{resourceToken}`
- Storage Account: `snippysto{resourceToken}`
- AI Foundry: `ai-foundry-snippy-{resourceToken}`
- Key Vault: `kv-snippy-{resourceToken}`

## Getting Deployment Outputs

After successful deployment, retrieve important configuration values:

```bash
# Get Function App URL (All levels)
az deployment sub show \
  --name level-X \
  --query properties.outputs.FUNCTION_APP_URL.value

# Get AI Project Connection String (Level 2+)
az deployment sub show \
  --name level-X \
  --query properties.outputs.AI_PROJECT_CONNECTION_STRING.value

# Get Key Vault URL (Level 6)
az deployment sub show \
  --name level-6 \
  --query properties.outputs.KEY_VAULT_URL.value
```

## Cost Optimization

**Progressive deployment saves costs:**
- Level 1: ~$10-20/month (Function App + Cosmos DB)
- Level 2: +$50-100/month (AI Foundry + models)
- Level 3: +$10-20/month (additional model)
- Level 4: +$5-10/month (blob storage)
- Level 5: No additional cost (configuration only)
- Level 6: +$10-15/month (Key Vault)

## Troubleshooting

### Common Issues

**Deployment Failures:**
- Check resource naming conflicts
- Verify region availability for AI services
- Ensure sufficient subscription quotas

**Permission Issues:**
- Verify Contributor role on subscription
- Check AI Foundry model availability in region

**Resource Dependencies:**
- Always deploy levels in order (1→2→3→4→5→6)
- Wait for deployment completion before deploying next level

### Support Commands

```bash
# Check deployment status
az deployment sub show --name level-X

# List all deployments
az deployment sub list --query "[].{Name:name,State:properties.provisioningState}"

# Clean up resources (delete resource group)
az group delete --name rg-snippy-hackathon-{environmentName}
```

## Next Steps

1. **Deploy Infrastructure**: Choose your target level and deploy
2. **Deploy Function Code**: Use VS Code Azure Functions extension
3. **Test Endpoints**: Verify health endpoint responds
4. **Follow Level Guides**: Complete challenges in `/hackathon/level-X.md`
5. **Monitor Progress**: Use Application Insights (Level 2+)
