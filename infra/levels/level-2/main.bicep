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
var tags = { 'azd-env-name': environmentName, project: 'snippy-ai-hackathon', level: 'level-2' }

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: 'rg-snippy-hackathon-${environmentName}'
  location: location
  tags: tags
}

// Deploy Level 1 resources first
module level1Resources '../level-1/resources.bicep' = {
  name: 'level1Resources'
  scope: rg
  params: {
    location: location
    resourceToken: resourceToken
    tags: tags
  }
}

// Add Level 2 resources (AI Services)
module level2Resources 'resources.bicep' = {
  name: 'level2Resources'
  scope: rg
  params: {
    location: location
    resourceToken: resourceToken
    tags: tags
    functionAppName: 'func-${resourceToken}'
    cosmosAccountName: 'cosmos-${resourceToken}'
  }
  dependsOn: [
    level1Resources
  ]
}

// ==================================
// Level 2 Outputs - Foundation + AI Services
// ==================================
@description('Base URL of the deployed Azure Function App')
output FUNCTION_APP_URL string = level1Resources.outputs.functionAppUrl

@description('Cosmos DB account endpoint URL for database operations')
output COSMOS_ENDPOINT string = level1Resources.outputs.cosmosEndpoint

@description('Name of the Cosmos DB database containing code snippets')
output COSMOS_DATABASE_NAME string = level1Resources.outputs.cosmosDatabaseName

@description('Name of the Cosmos DB container storing code snippets with vector embeddings')
output COSMOS_CONTAINER_NAME string = level1Resources.outputs.cosmosContainerName

// AI outputs (New in Level 2)
@description('Connection string for the AI Foundry project API endpoints')
output AI_PROJECT_CONNECTION_STRING string = level2Resources.outputs.aiProjectConnectionString

@description('Name of the AI Foundry project for organizing AI resources')
output AI_FOUNDRY_PROJECT_NAME string = level2Resources.outputs.aiFoundryProjectName

@description('OpenAI-compatible endpoint URL for the AI Foundry service')
output AI_FOUNDRY_OPENAI_ENDPOINT string = level2Resources.outputs.aiFoundryOpenAiEndpoint

@description('Name of the deployed embedding model for text vectorization')
output EMBEDDING_MODEL_DEPLOYMENT_NAME string = level2Resources.outputs.embeddingModelDeploymentName

@description('Health check endpoint to verify deployment')
output HEALTH_ENDPOINT string = '${level1Resources.outputs.functionAppUrl}/api/health'

@description('Snippets API endpoint for CRUD operations')
output SNIPPETS_ENDPOINT string = '${level1Resources.outputs.functionAppUrl}/api/snippets'

@description('Embeddings orchestrator endpoint for vector generation')
output EMBEDDINGS_ENDPOINT string = '${level1Resources.outputs.functionAppUrl}/api/orchestrators/embeddings'
