# ⚡ Azure Deployment Guide

Quick reference for deploying and managing your Snippy AI infrastructure using Azure Developer CLI (azd).

## 🚀 Essential Commands

### Initial Setup
```bash
# Authenticate
az login
azd auth login

# Create environment
azd env new "your-team-name-hackathon"

# Deploy everything (infrastructure + application)
azd up
```

### Development Workflow
```bash
# Deploy code changes only
azd deploy

# Deploy infrastructure changes
azd provision

# Deploy everything (if unsure)
azd up
```

### Monitoring & Debugging
```bash
# View environment variables
azd env get-values

# Get deployment outputs
azd env get-values | grep -E "(FUNCTION_APP_URL|COSMOS_ENDPOINT|STORAGE_ACCOUNT)"

# View deployment logs
azd provision --debug
```

### Cleanup
```bash
# Remove all Azure resources
azd down
```

## 🎯 What azd up Deploys

The `azd up` command creates this complete infrastructure:

| **Resource** | **Purpose** | **Configuration** |
|--------------|-------------|-------------------|
| **Function App** | API and orchestration | Python 3.11, consumption plan |
| **Cosmos DB** | Vector database | Serverless, vector search enabled |
| **Storage Account** | Document storage | Hot tier, hierarchical namespace |
| **AI Foundry** | AI models | GPT-4o + text-embedding-3-small |
| **App Insights** | Monitoring | Connected to Function App |
| **Log Analytics** | Centralized logs | Shared workspace |
| **Managed Identity** | Secure auth | No API keys needed |

## 🔧 Configuration

After deployment, your application configuration is automatically set:
- Connection strings for all services
- AI model endpoints and versions
- Security settings and managed identities
- Monitoring and logging configuration

## 🧪 Quick Test

```bash
# Test deployment
curl https://your-function-app.azurewebsites.net/api/health

# Upload test document
echo "# Test Doc\nSample content" > test.md
az storage blob upload \
  --file test.md \
  --container-name snippet-input \
  --name test.md \
  --account-name your-storage-account

# Query the knowledge base
curl -X POST https://your-function-app.azurewebsites.net/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test document", "max_results": 3}'
```

## 🎯 Pro Tips

- **Region Selection**: Use `eastus2` for best model availability
- **Environment Names**: Use descriptive names like `team1-hackathon-dev`
- **Monitoring**: Check Azure Portal → Application Insights for detailed logs
- **Costs**: All services use consumption/serverless tiers to minimize costs
- **Cleanup**: Always run `azd down` when finished to avoid charges

---

**Ready to deploy?** Run `azd up` and start building! 🚀
