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

param apiServiceName string = ''
param apiUserAssignedIdentityName string = ''
param applicationInsightsName string = ''
param appServicePlanName string = ''
param logAnalyticsName string = ''
param resourceGroupName string = ''
param storageAccountName string = ''
param disableLocalAuth bool = true

@allowed(['gpt-4o'])
param chatModelName string = 'gpt-4o'

@allowed(['text-embedding-3-small'])
param embeddingModelName string = 'text-embedding-3-small'

import * as regionSelector from './app/region-selector.bicep'
var abbrs = loadJsonContent('./abbreviations.json')

var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }
var functionAppName = !empty(apiServiceName) ? apiServiceName : '${abbrs.webSitesFunctions}api-${resourceToken}'
var deploymentStorageContainerName = 'app-package-${take(functionAppName, 32)}-${take(toLower(uniqueString(functionAppName, resourceToken)), 7)}'

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

// User assigned managed identity to be used by the function app
module apiUserAssignedIdentity './core/identity/userAssignedIdentity.bicep' = {
  name: 'apiUserAssignedIdentity'
  scope: rg
  params: {
    location: location
    tags: tags
    identityName: !empty(apiUserAssignedIdentityName) ? apiUserAssignedIdentityName : '${abbrs.managedIdentityUserAssignedIdentities}api-${resourceToken}'
  }
}

// The application backend is a function app
module appServicePlan './core/host/appserviceplan.bicep' = {
  name: 'appserviceplan'
  scope: rg
  params: {
    name: !empty(appServicePlanName) ? appServicePlanName : '${abbrs.webServerFarms}${resourceToken}'
    location: regionSelector.getFlexConsumptionRegion(location)
    tags: tags
    sku: {
      name: 'FC1'
      tier: 'FlexConsumption'
    }
  }
}

// Backing storage for Azure functions api
module storage './core/storage/storage-account.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    name: !empty(storageAccountName) ? storageAccountName : '${abbrs.storageStorageAccounts}${resourceToken}'
    location: location
    tags: tags
    containers: [{name: deploymentStorageContainerName}, {name: 'snippets'}]
    publicNetworkAccess: 'Enabled'
  }
}

var StorageBlobDataOwner = 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
var StorageQueueDataContributor = '974c5e8b-45b9-4653-ba55-5f855dd0fb88'

// Allow access from api to blob storage using a managed identity
module blobRoleAssignmentApi 'app/storage-Access.bicep' = {
  name: 'blobRoleAssignmentapi'
  scope: rg
  params: {
    storageAccountName: storage.outputs.name
    roleDefinitionID: StorageBlobDataOwner
    principalID: apiUserAssignedIdentity.outputs.identityPrincipalId
  }
}

// Allow access from api to queue storage using a managed identity
module queueRoleAssignmentApi 'app/storage-Access.bicep' = {
  name: 'queueRoleAssignmentapi'
  scope: rg
  params: {
    storageAccountName: storage.outputs.name
    roleDefinitionID: StorageQueueDataContributor
    principalID: apiUserAssignedIdentity.outputs.identityPrincipalId
  }
}

// Monitor application with Azure Monitor
module monitoring './core/monitor/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    location: location
    tags: tags
    logAnalyticsName: !empty(logAnalyticsName) ? logAnalyticsName : '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    applicationInsightsName: !empty(applicationInsightsName) ? applicationInsightsName : '${abbrs.insightsComponents}${resourceToken}'
    disableLocalAuth: disableLocalAuth  
  }
}

var monitoringRoleDefinitionId = '3913510d-42f4-4e42-8a64-420c390055eb' // Monitoring Metrics Publisher role ID

// Allow access from api to application insights using a managed identity
module appInsightsRoleAssignmentApi './core/monitor/appinsights-access.bicep' = {
  name: 'appInsightsRoleAssignmentapi'
  scope: rg
  params: {
    appInsightsName: monitoring.outputs.applicationInsightsName
    roleDefinitionID: monitoringRoleDefinitionId
    principalID: apiUserAssignedIdentity.outputs.identityPrincipalId
  }
}

// Azure OpenAI for embeddings
module openai './core/ai/cognitive-services.bicep' = {
  name: 'openai'
  scope: rg
  params: {
    location: regionSelector.getCognitiveServicesRegion(location, chatModelName, embeddingModelName)
    tags: tags
    chatModelName: chatModelName
    aiServicesName: '${abbrs.cognitiveServicesAccounts}${resourceToken}'
    embeddingModelName: embeddingModelName
  }
}

// Azure Cosmos DB for snippet storage
module cosmosDb './core/database/cosmos-db.bicep' = {
  name: 'cosmosDb'
  scope: rg
  params: {
    location: location
    tags: tags
    accountName: '${abbrs.documentDBDatabaseAccounts}${resourceToken}'
    aiServicesName: openai.outputs.aiServicesName
  }
}

module keyVault './app/key-vault.bicep' = {
  name: 'keyVault'
  scope: rg
  params: {
    location: location
    keyVaultName: '${abbrs.keyVaultVaults}${resourceToken}'
  }
}

// Azure AI Hub and Project for code analysis
module aiProject './core/ai/ai-project.bicep' = {
  name: 'aiProject'
  scope: rg
  params: {
    location: location
    tags: tags
    aiHubName: '${abbrs.machineLearningServicesWorkspaces}hub-${resourceToken}'
    aiProjectName: '${abbrs.machineLearningServicesWorkspaces}proj-${resourceToken}'
    storageAccountId: storage.outputs.id
    keyVaultId: keyVault.outputs.keyVaultId
    aiServicesEndpoint: openai.outputs.aiServicesEndpoint
    aiServicesId: openai.outputs.aiServicesId
    aiServicesName: openai.outputs.aiServicesName
  }
}

// Allow access from api to AI Project
var AzureAiDeveloper = '64702f94-c441-49e6-a78b-ef80e0188fee'
module aiProjectRoleAssignmentApi 'app/ai-project-Access.bicep' = {
  name: 'aiProjectRoleAssignmentApi'
  scope: rg
  params: {
    aiProjectName: aiProject.outputs.aiProjectName
    roleDefinitionId: AzureAiDeveloper
    principalId: apiUserAssignedIdentity.outputs.identityPrincipalId
  }
}

module api './app/api.bicep' = {
  name: 'api'
  scope: rg
  params: {
    name: functionAppName
    location: regionSelector.getFlexConsumptionRegion(location)
    tags: tags
    applicationInsightsName: monitoring.outputs.applicationInsightsName
    appServicePlanId: appServicePlan.outputs.id
    runtimeName: 'python'
    runtimeVersion: '3.11'
    storageAccountName: storage.outputs.name
    deploymentStorageContainerName: deploymentStorageContainerName
    identityId: apiUserAssignedIdentity.outputs.identityId
    identityClientId: apiUserAssignedIdentity.outputs.identityClientId
    aiServicesId: openai.outputs.aiServicesId
    appSettings: {
      COSMOS_CONN: cosmosDb.outputs.connectionString
      COSMOS_DATABASE_NAME: cosmosDb.outputs.databaseName
      COSMOS_CONTAINER_NAME: cosmosDb.outputs.containerName
      BLOB_CONTAINER_NAME: 'snippet-backups'
      EMBEDDING_MODEL_DEPLOYMENT_NAME: openai.outputs.embeddingDeploymentName
      AGENTS_MODEL_DEPLOYMENT_NAME: 'gpt-4o'
      COSMOS_VECTOR_TOP_K: '30'
      PROJECT_CONNECTION_STRING: aiProject.outputs.projectConnectionString
      AZURE_OPENAI_ENDPOINT: openai.outputs.aiServicesEndpoint
      PYTHON_ENABLE_WORKER_EXTENSIONS: '1'
      AzureWebJobsFeatureFlags: 'EnableWorkerIndexing'
      AZURE_CLIENT_ID: apiUserAssignedIdentity.outputs.identityClientId
    }
  }
}

// ==================================
// Outputs
// ==================================
// Define outputs needed specifically for configuring local.settings.json
// Use 'azd env get-values' to retrieve these after provisioning.
// WARNING: Secrets (Keys, Connection Strings) are output directly and will be visible in deployment history.
// Output names directly match the corresponding keys in local.settings.json for easier mapping.

@description('Cosmos DB connection string (includes key). Output name matches the COSMOS_CONN key in local settings.')
output COSMOS_CONN string = cosmosDb.outputs.connectionString

@description('Connection string for the Azure AI Project. Output name matches the PROJECT_CONNECTION_STRING key in local settings.')
output PROJECT_CONNECTION_STRING string = aiProject.outputs.projectConnectionString

@description('Endpoint for Azure OpenAI services. Output name matches the AZURE_OPENAI_ENDPOINT key in local settings.')
output AZURE_OPENAI_ENDPOINT string = openai.outputs.azureOpenAIServiceEndpoint

@description('Primary key for Azure OpenAI services. Output name matches the AZURE_OPENAI_KEY key in local settings.')
// @secure() - issue with latest bicep version, set secure in cognitive services module
output AZURE_OPENAI_KEY string = openai.outputs.primaryKey

@description('Name of the deployed Azure Function App.')
output AZURE_FUNCTION_NAME string = api.outputs.SERVICE_API_NAME // Function App Name

