param location string
param resourceToken string
param tags object
param functionAppName string
param cosmosAccountName string

// ==================================
// Level 2: AI Services Addition
// - Azure AI Foundry (OpenAI services)
// - Embedding model deployment
// - Vector search capability for Cosmos DB
// - Application Insights for monitoring
// ==================================

// Reference existing Function App to update settings
resource functionApp 'Microsoft.Web/sites@2024-11-01' existing = {
  name: functionAppName
}

// Reference existing Cosmos DB to add vector search capability
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2025-04-15' existing = {
  name: cosmosAccountName
}

// Update Cosmos DB to enable vector search
resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2025-04-15' existing = {
  parent: cosmosAccount
  name: 'dev-snippet-db'
}

// Update container with vector indexing policy
resource cosmosContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-04-15' = {
  parent: cosmosDatabase
  name: 'code-snippets-vectors'
  properties: {
    resource: {
      id: 'code-snippets-vectors'
      partitionKey: {
        paths: ['/name']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/embedding/*'
          }
        ]
        vectorIndexes: [
          {
            path: '/embedding'
            type: 'quantizedFlat'
          }
        ]
      }
    }
  }
}

// Log Analytics Workspace for Application Insights
module logAnalytics 'br/public:avm/res/operational-insights/workspace:0.7.0' = {
  name: 'loganalytics'
  params: {
    name: 'log-${resourceToken}'
    location: location
    tags: tags
  }
}

// Application Insights
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appins-${resourceToken}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.outputs.resourceId
  }
  tags: tags
}

// AI Foundry (OpenAI Services)
resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: 'ai-foundry-snippy-${resourceToken}'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  properties: {
    publicNetworkAccess: 'Enabled'
    allowProjectManagement: true
    customSubDomainName: 'ai-foundry-snippy-${resourceToken}'
    disableLocalAuth: false
  }
  tags: tags
}

// AI Project
resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  name: 'snippy'
  parent: aiFoundry
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
  tags: tags
}

// Embedding model deployment
resource modelDeployment_embedding 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: aiFoundry
  name: 'text-embedding-3-small'
  sku: {
    capacity: 1
    name: 'GlobalStandard'
  }
  properties: {
    model: {
      name: 'text-embedding-3-small'
      format: 'OpenAI'
    }
  }
}

// Update Function App settings to enable AI services
resource functionAppSettings 'Microsoft.Web/sites/config@2024-11-01' = {
  parent: functionApp
  name: 'appsettings'
  properties: {
    FUNCTIONS_WORKER_RUNTIME: 'python'
    FUNCTIONS_EXTENSION_VERSION: '~4'
    AzureWebJobsStorage: functionApp.listkeys().keys[0].value // Keep existing storage connection
    PYTHON_ENABLE_WORKER_EXTENSIONS: 'True'
    DISABLE_OPENAI: '0' // Enable AI services for Level 2
    COSMOS_ENDPOINT: cosmosAccount.properties.documentEndpoint
    COSMOS_DATABASE_NAME: 'dev-snippet-db'
    COSMOS_CONTAINER_NAME: 'code-snippets-vectors'
    COSMOS_VECTOR_TOP_K: '5'
    CHUNK_SIZE: '800'
    APPINSIGHTS_INSTRUMENTATIONKEY: applicationInsights.properties.InstrumentationKey
    APPLICATIONINSIGHTS_CONNECTION_STRING: applicationInsights.properties.ConnectionString
    AI_PROJECT_CONNECTION_STRING: 'https://${aiFoundry.properties.customSubDomainName}.services.ai.azure.com/api/projects/${aiProject.name}'
    AI_FOUNDRY_OPENAI_ENDPOINT: 'https://${aiFoundry.properties.customSubDomainName}.openai.azure.com'
    EMBEDDING_MODEL_DEPLOYMENT_NAME: modelDeployment_embedding.name
  }
}

// RBAC: Grant Function App access to AI Foundry
resource functionAppAiFoundryUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiFoundry.id, functionApp.id, 'CognitiveServicesOpenAIUser')
  scope: aiFoundry
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    ) // Cognitive Services OpenAI User
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
  dependsOn: [
    modelDeployment_embedding
  ]
}

// RBAC: Grant Function App access to Application Insights
var monitoringMetricsPublisherId = '3913510d-42f4-4e42-8a64-420c390055eb'
resource roleAssignmentAppInsights 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(applicationInsights.id, functionApp.id, monitoringMetricsPublisherId)
  scope: applicationInsights
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringMetricsPublisherId)
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ==================================
// Outputs
// ==================================
output aiProjectConnectionString string = 'https://${aiFoundry.properties.customSubDomainName}.services.ai.azure.com/api/projects/${aiProject.name}'
output aiFoundryProjectName string = aiProject.name
output aiFoundryOpenAiEndpoint string = 'https://${aiFoundry.properties.customSubDomainName}.openai.azure.com'
output embeddingModelDeploymentName string = modelDeployment_embedding.name
output appInsightsConnectionString string = applicationInsights.properties.ConnectionString
