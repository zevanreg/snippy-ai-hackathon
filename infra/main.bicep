targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
@allowed(['eastus', 'eastus2', 'westus', 'westus2', 'westus3'])
@metadata({
  azd: {
    type: 'location'
  }
})
param location string
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName, project: 'snippy-ai-hackathon' }

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: 'snippy-ai-hackathon'
  location: location
  tags: tags
}

module hackathonResources 'hackathon-resources.bicep' = {
  name: 'hackathonResources'
  scope: rg
  params: {
    location: location
    resourceToken: resourceToken
    tags: tags
  }
}

// // Deploy resources using a module in the resource group scope
// module resources 'simple-resources.bicep' = {
//   name: 'simpleResources'
//   scope: rg
//   params: {
//     location: location
//     resourceToken: resourceToken
//     tags: tags
//   }
// }

// // Output the Function App URL
// output REACT_APP_API_BASE_URL string = resources.outputs.functionAppUrl
// output SERVICE_API_ENDPOINTS array = resources.outputs.endpoints
// output AZUREWEBJOBSSTORAGE string = resources.outputs.storageConnectionString


// ==================================
// Outputs
// ==================================
// Define outputs needed specifically for configuring local.settings.json
// Use 'azd env get-values' to retrieve these after provisioning.
// WARNING: Secrets (Keys, Connection Strings) are output directly and will be visible in deployment history.
// Output names directly match the corresponding keys in local.settings.json for easier mapping.

@description('Name of the Azure Storage Account for blob storage operations')
output STORAGE_ACCOUNT_NAME string = hackathonResources.outputs.storageAccountName

@description('Connection string for the Azure Storage Account. Used for AzureWebJobsStorage and blob operations')
output STORAGE_CONNECTION_STRING string = hackathonResources.outputs.storageConnectionString

@description('Name of the blob container for snippet input files')
output STORAGE_CONTAINER_SNIPPETINPUT string = hackathonResources.outputs.storageBlobContainerSnippetInputs

@description('Name of the blob container for snippet backup files')
output STORAGE_CONTAINER_SNIPPETBACKUPS string = hackathonResources.outputs.storageBlobContainerSnippetBackups

@description('Cosmos DB account endpoint URL for database operations')
output COSMOS_ENDPOINT string = hackathonResources.outputs.cosmosEndpoint

@description('Name of the Cosmos DB database containing code snippets')
output COSMOS_DATABASE_NAME string = hackathonResources.outputs.cosmosDatabaseName

@description('Name of the Cosmos DB container storing code snippets with vector embeddings')
output COSMOS_CONTAINER_NAME string = hackathonResources.outputs.cosmosContainerName

@description('Connection string for the AI Foundry project API endpoints')
output AI_PROJECT_CONNECTION_STRING string = hackathonResources.outputs.aiProjectConnectionString

@description('Name of the AI Foundry project for organizing AI resources')
output AI_FOUNDRY_PROJECT_NAME string = hackathonResources.outputs.aiFoundryProjectName

@description('OpenAI-compatible endpoint URL for the AI Foundry service')
output AI_FOUNDRY_OPENAI_ENDPOINT string = hackathonResources.outputs.aiFoundryOpenAiEndpoint

@description('Primary access key for the AI Foundry OpenAI service')
output AI_FOUNDRY_OPENAI_KEY string = hackathonResources.outputs.aiFoundryOpenAiKey

@description('Name of the deployed embedding model for text vectorization')
output EMBEDDING_MODEL_DEPLOYMENT_NAME string = hackathonResources.outputs.embeddingModelDeploymentName

@description('Name of the deployed chat model for conversational AI')
output CHAT_MODEL_DEPLOYMENT_NAME string = hackathonResources.outputs.chatModelDeploymentName

@description('Type/name of the chat model (e.g., gpt-4o)')
output CHAT_MODEL_DEPLOYMENT_TYPE string = hackathonResources.outputs.chatModelDeploymentType

@description('Base URL of the deployed Azure Function App')
output FUNCTION_APP_URL string = hackathonResources.outputs.functionAppUrl

// @description('Array of available API endpoints for the Function App')
// output ENDPOINTS array = hackathonResources.outputs.endpoints

@description('Connection string for Application Insights telemetry and monitoring')
output APP_INSIGHTS_CONNECTION_STRING string = hackathonResources.outputs.appInsightsConnectionString

