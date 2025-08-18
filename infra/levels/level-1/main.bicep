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
var tags = { 'azd-env-name': environmentName, project: 'snippy-ai-hackathon', level: 'level-1' }

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: 'rg-snippy-hackathon-${environmentName}'
  location: location
  tags: tags
}

module level1Resources 'resources.bicep' = {
  name: 'level1Resources'
  scope: rg
  params: {
    location: location
    resourceToken: resourceToken
    tags: tags
  }
}

// ==================================
// Level 1 Outputs - Foundation
// ==================================
@description('Base URL of the deployed Azure Function App')
output FUNCTION_APP_URL string = level1Resources.outputs.functionAppUrl

@description('Cosmos DB account endpoint URL for database operations')
output COSMOS_ENDPOINT string = level1Resources.outputs.cosmosEndpoint

@description('Name of the Cosmos DB database containing code snippets')
output COSMOS_DATABASE_NAME string = level1Resources.outputs.cosmosDatabaseName

@description('Name of the Cosmos DB container storing code snippets')
output COSMOS_CONTAINER_NAME string = level1Resources.outputs.cosmosContainerName

@description('Health check endpoint to verify deployment')
output HEALTH_ENDPOINT string = '${level1Resources.outputs.functionAppUrl}/api/health'

@description('Snippets API endpoint for CRUD operations')
output SNIPPETS_ENDPOINT string = '${level1Resources.outputs.functionAppUrl}/api/snippets'
