targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
@allowed(['eastus', 'eastus2', 'westus', 'westus2', 'westus3'])
param location string

var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName, project: 'snippy-ai-hackathon', level: 'level-6' }

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: 'rg-snippy-hackathon-${environmentName}'
  location: location
  tags: tags
}

// Deploy all previous levels
module level1Resources '../level-1/resources.bicep' = {
  name: 'level1Resources'
  scope: rg
  params: {
    location: location
    resourceToken: resourceToken
    tags: tags
  }
}

module level2Resources '../level-2/resources.bicep' = {
  name: 'level2Resources'
  scope: rg
  params: {
    location: location
    resourceToken: resourceToken
    tags: tags
    functionAppName: 'func-${resourceToken}'
    cosmosAccountName: 'cosmos-${resourceToken}'
  }
  dependsOn: [level1Resources]
}

module level3Resources '../level-3/resources.bicep' = {
  name: 'level3Resources'
  scope: rg
  params: {
    resourceToken: resourceToken
    functionAppName: 'func-${resourceToken}'
    aiFoundryName: 'ai-foundry-snippy-${resourceToken}'
  }
  dependsOn: [level2Resources]
}

module level4Resources '../level-4/resources.bicep' = {
  name: 'level4Resources'
  scope: rg
  params: {
    functionAppName: 'func-${resourceToken}'
    storageAccountName: 'snippysto${resourceToken}'
  }
  dependsOn: [level3Resources]
}

module level5Resources '../level-5/resources.bicep' = {
  name: 'level5Resources'
  scope: rg
  dependsOn: [level4Resources]
}

// Add Level 6 resources (Zero Trust Security)
module level6Resources 'resources.bicep' = {
  name: 'level6Resources'
  scope: rg
  params: {
    location: location
    resourceToken: resourceToken
    tags: tags
    functionAppName: 'func-${resourceToken}'
  }
  dependsOn: [level5Resources]
}

// ==================================
// Level 6 Outputs - Complete Secure Platform
// ==================================
@description('Base URL of the deployed Azure Function App')
output FUNCTION_APP_URL string = level1Resources.outputs.functionAppUrl

@description('Cosmos DB account endpoint URL for database operations')
output COSMOS_ENDPOINT string = level1Resources.outputs.cosmosEndpoint

@description('Name of the Cosmos DB database containing code snippets')
output COSMOS_DATABASE_NAME string = level1Resources.outputs.cosmosDatabaseName

@description('Name of the Cosmos DB container storing code snippets with vector embeddings')
output COSMOS_CONTAINER_NAME string = level1Resources.outputs.cosmosContainerName

// AI outputs
@description('Connection string for the AI Foundry project API endpoints')
output AI_PROJECT_CONNECTION_STRING string = level2Resources.outputs.aiProjectConnectionString

@description('Name of the AI Foundry project for organizing AI resources')
output AI_FOUNDRY_PROJECT_NAME string = level2Resources.outputs.aiFoundryProjectName

@description('OpenAI-compatible endpoint URL for the AI Foundry service')
output AI_FOUNDRY_OPENAI_ENDPOINT string = level2Resources.outputs.aiFoundryOpenAiEndpoint

@description('Name of the deployed embedding model for text vectorization')
output EMBEDDING_MODEL_DEPLOYMENT_NAME string = level2Resources.outputs.embeddingModelDeploymentName

@description('Name of the deployed chat model for conversational AI')
output CHAT_MODEL_DEPLOYMENT_NAME string = level3Resources.outputs.chatModelDeploymentName

@description('Type/name of the chat model (e.g., gpt-4o)')
output CHAT_MODEL_DEPLOYMENT_TYPE string = level3Resources.outputs.chatModelDeploymentType

// Storage outputs
@description('Name of the Azure Storage Account for blob storage operations')
output STORAGE_ACCOUNT_NAME string = level1Resources.outputs.storageAccountName

@description('Name of the blob container for snippet input files')
output STORAGE_CONTAINER_SNIPPETINPUT string = level4Resources.outputs.storageBlobContainerSnippetInputs

@description('Name of the blob container for snippet backup files')
output STORAGE_CONTAINER_SNIPPETBACKUPS string = level4Resources.outputs.storageBlobContainerSnippetBackups

@description('Connection string for Application Insights telemetry and monitoring')
output APP_INSIGHTS_CONNECTION_STRING string = level2Resources.outputs.appInsightsConnectionString

// Security outputs (New in Level 6)
@description('Key Vault URL for secure credential storage')
output KEY_VAULT_URL string = level6Resources.outputs.keyVaultUrl

@description('Managed identity client ID for secure Azure service authentication')
output MANAGED_IDENTITY_CLIENT_ID string = level6Resources.outputs.managedIdentityClientId

// API Endpoints
@description('Health check endpoint to verify deployment')
output HEALTH_ENDPOINT string = '${level1Resources.outputs.functionAppUrl}/api/health'

@description('Snippets API endpoint for CRUD operations')
output SNIPPETS_ENDPOINT string = '${level1Resources.outputs.functionAppUrl}/api/snippets'

@description('Embeddings orchestrator endpoint for vector generation')
output EMBEDDINGS_ENDPOINT string = '${level1Resources.outputs.functionAppUrl}/api/orchestrators/embeddings'

@description('Query endpoint for vector search and chat completions')
output QUERY_ENDPOINT string = '${level1Resources.outputs.functionAppUrl}/api/query'

@description('Ingestion endpoint for blob-triggered snippet processing')
output INGESTION_ENDPOINT string = '${level1Resources.outputs.functionAppUrl}/api/orchestrators/ingestion'

@description('Multi-agent orchestrator endpoint for complex AI workflows')
output MULTI_AGENT_ENDPOINT string = '${level1Resources.outputs.functionAppUrl}/api/orchestrators/multi-agent'
