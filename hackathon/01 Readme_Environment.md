# Azure Developer CLI (azd) Environment Setup

## What azd Does in the Snippy AI Hackathon Project

Azure Developer CLI (azd) streamlines the deployment of the complete Snippy AI infrastructure and application. In this project, azd orchestrates a three-step workflow: **Infrastructure → Local Settings → Application**.

### The Snippy AI azd Workflow:

1. **🏗️ Infrastructure Deployment**: Provisions all Azure resources using Bicep templates
2. **⚙️ Configuration Generation**: Creates local development settings from deployed resources
3. **🚀 Application Deployment**: Builds and deploys the Python Function App

## Quick Start

### 1. Deploy Everything
```bash
# Login and deploy complete environment
azd auth login
azd env new "NAME OF YOUR ENVIRONMENT"
azd up
```

This single command will:
- Create all Azure resources by looking for a `main.bicep` file in the `infra`folder
- run the bicep deployment
- store the outputs in the azd environment as variables
- Deploy the Function App
- set the right values in `local.host.settings` from the azd environment variables

## What Gets Deployed (Infrastructure Phase)

The `azd up` command deploys this complete AI infrastructure:

| **Service** | **Purpose** | **Configuration** |
|-------------|-------------|-------------------|
| **Storage Account** | Blob storage for documents and data | Hot tier, hierarchical namespace |
| **Cosmos DB** | Vector database for AI embeddings | Serverless, vector search enabled |
| **Function App** | API and orchestration layer | Python 3.11, consumption plan |
| **AI Foundry** | AI model hosting and inference | GPT-4o + text-embedding-3-small |
| **Application Insights** | Monitoring and logging | Connected to Function App |
| **Log Analytics** | Centralized logging workspace | Shared across all services |
| **Managed Identities** | Secure service-to-service auth | No API keys needed |

## Configuration Generation (Local Settings Phase)

After deployment, the `generate-settings` scripts extract outputs from Azure and create your local development configuration:

```json
// Generated src/local.settings.json structure
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "DefaultEndpointsProtocol=https;AccountName=...",
    "COSMOS_ENDPOINT": "https://your-cosmos.documents.azure.com:443/",
    "COSMOS_DATABASE_NAME": "hackathon",
    "OPENAI_ENDPOINT": "https://your-ai-foundry.cognitiveservices.azure.com/",
    "OPENAI_API_VERSION": "2024-02-01",
    "BLOB_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;...",
    // ... other service endpoints
  }
}
```

### What the Scripts Do:
1. **Extract azd outputs**: Reads all deployed resource information
2. **Map to Function App settings**: Converts Azure resource data to app configuration
3. **Generate local.settings.json**: Creates file for local development
4. **Enable local debugging**: Your dev environment matches production

## Alternative azd Commands

### Step-by-Step Deployment
```bash
# Initialize environment
azd init

# Deploy only infrastructure 
azd provision

# Deploy only application code
azd deploy
azd env get-values
```

## Deployed Resources

The `azd up` command creates the following Azure resources:

### Core Infrastructure:
- **Resource Group**: `snippy-ai-hackathon`
- **Storage Account**: For blob storage and Function App content
- **Cosmos DB**: Serverless account with vector search capabilities
- **Function App**: Python 3.11 runtime with managed identity
- **App Service Plan**: Consumption tier for serverless functions

### AI Services:
- **AI Foundry**: Cognitive Services account for AI operations
- **AI Project**: Project-based AI resource management
- **Model Deployments**:
  - GPT-4o for chat completions
  - text-embedding-3-small for embeddings

### Monitoring:
- **Log Analytics Workspace**: Centralized logging
- **Application Insights**: Application performance monitoring

```

### Environment Management
```bash
# View deployment status
azd env list
azd env show

# Get deployed resource values  
azd env get-values

# Tear down when finished
azd down
```

## Local Development Setup (Application Phase)

Once infrastructure is deployed and local settings generated, you can develop locally:

### Starting the Function App:
```bash
cd src

# Activate virtual environment (if needed)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start functions locally
func start
```

### Testing the Deployment:
```bash
# Test API endpoints
curl http://localhost:7071/api/health

# View function logs
# Logs appear in terminal and Application Insights
```

### What You Get Locally:
- **AI Services**: Connected to deployed AI Foundry models
- **Vector Database**: Connected to Cosmos DB with vector search
- **Storage**: Connected to Azure Blob Storage
- **Monitoring**: Logs sent to Application Insights
- **Authentication**: Uses your Azure CLI credentials for local development

## Environment Management

### Getting Resource Information
```bash
# View all deployed resource endpoints
azd env get-values

# Get specific values for troubleshooting
azd env get-values | grep FUNCTION_APP_URL
azd env get-values | grep COSMOS_ENDPOINT
```

### Cleanup
```bash
# Remove all Azure resources when done
azd down
```

## Troubleshooting Common Issues

### Deployment Failures
```bash
# Check deployment logs
azd provision --debug

# View Azure portal for resource status
# Check Application Insights for runtime errors
```

### Local Development Issues
```bash
# Regenerate local settings if needed
./scripts/generate-settings.sh

# Verify Azure CLI authentication
az account show
azd auth login

# Check function app logs
func start --verbose
```
## Cleanup and Teardown

### Remove All Resources
```bash
# Delete all Azure resources
azd down
```

This command:
- Deletes the entire resource group
- Removes all Azure resources
- Preserves local configuration for redeployment

### Selective Cleanup
```bash
# Remove only the application (keep infrastructure)
azd deploy --tear-down

# Remove environment configuration
azd env delete <environment-name>
```

## Troubleshooting

### Common Issues:

**Authentication Problems:**
```bash
# Re-authenticate
azd auth login
az login --tenant <your-tenant-id>
```

**Permission Errors:**
- Ensure you have Contributor/Owner role on the subscription
- Check resource provider registrations

**Deployment Failures:**
```bash
# View detailed logs
azd provision --debug

# Check Azure portal for specific error messages
```

**Resource Naming Conflicts:**
- Choose a different environment name
- Ensure globally unique resource names

### Getting Help:
```bash
# azd help
azd --help
azd provision --help

# View deployment status
azd env show
```

## Next Steps

After successful environment setup:

1. **Explore Function Endpoints**: Test the deployed API endpoints
2. **Review Monitoring**: Check Application Insights for telemetry
3. **Develop Locally**: Use the generated local.settings.json
4. **Customize Infrastructure**: Modify Bicep templates as needed
5. **Set Up CI/CD**: Use azd pipeline templates for automation

## Additional Resources

- [Azure Developer CLI Documentation](https://docs.microsoft.com/en-us/azure/developer/azure-developer-cli/)
- [Azure Functions Documentation](https://docs.microsoft.com/en-us/azure/azure-functions/)
- [Azure AI Foundry Documentation](https://docs.microsoft.com/en-us/azure/ai-services/)
- [Project Repository](https://github.com/cihanduruer/snippy-ai-hackathon)

---

**Ready to start building? Run `azd up` and you'll have a complete AI-powered development environment in minutes!** 🚀
