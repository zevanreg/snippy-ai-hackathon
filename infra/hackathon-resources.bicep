param location string

param resourceToken string

param tags object

resource storage 'Microsoft.Storage/storageAccounts@2025-01-01' = {
  name: 'snippysto${resourceToken}'
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
  }
  tags: tags
}

// Cosmos DB Account with vector search capabilities
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2025-04-15' = {
  name: 'cosmos-${resourceToken}'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'
      }
      {
        name: 'EnableNoSQLVectorSearch'
      }
    ]
  }
  tags: tags
}

// Cosmos DB Database
resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2025-04-15' = {
  parent: cosmosAccount
  name: 'dev-snippet-db'
  properties: {
    resource: {
      id: 'dev-snippet-db'
    }
  }
}

// Cosmos DB Container with basic indexing (vector policy will be configured via code)
resource cosmosContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-04-15' = {
  parent: cosmosDatabase
  name: 'code-snippets'
  properties: {
    resource: {
      id: 'code-snippets'
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
      }
    }
  }
}

// Function App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2024-11-01' = {
  name: 'asp-${resourceToken}'
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  properties: {
    reserved: true
  }
  kind: 'linux'
  tags: tags
}

// Function App
resource functionApp 'Microsoft.Web/sites@2024-11-01' = {
  name: 'func-${resourceToken}'
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    reserved: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appSettings: [
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
        {
          name: 'PYTHON_ENABLE_WORKER_EXTENSIONS'
          value: 'True'
        }
        {
          name: 'DISABLE_OPENAI'
          value: '1'
        }
        {
          name: 'COSMOS_ENDPOINT'
          value: cosmosAccount.properties.documentEndpoint
        }
        {
          name: 'COSMOS_DATABASE_NAME'
          value: 'dev-snippet-db'
        }
        {
          name: 'COSMOS_CONTAINER_NAME'
          value: 'code-snippets'
        }
        {
          name: 'COSMOS_VECTOR_TOP_K'
          value: '5'
        }
        {
          name: 'CHUNK_SIZE'
          value: '800'
        }
      ]
      cors: {
        allowedOrigins: ['*']
        supportCredentials: false
      }
    }
  }
  tags: union(tags, { 'azd-service-name': 'api' })
}

// RBAC: Grant Function App access to Cosmos DB
resource cosmosDbContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(cosmosAccount.id, functionApp.id, 'CosmosDBContributor')
  scope: cosmosAccount
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'b24988ac-6180-42a0-ab88-20f7382dd24c'
    ) // Cosmos DB Built-in Data Contributor
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

module logAnalytics 'br/public:avm/res/operational-insights/workspace:0.7.0' = {
  name: 'loganalytics'
  params: {
    name: 'log-${resourceToken}'
    location: location
    tags: tags
  }
}

module applicationInsights 'br/public:avm/res/insights/component:0.4.1' = {
  name: 'applicationinsights'
  params: {
    name: 'appins-${resourceToken}'
    location: location
    tags: tags
    workspaceResourceId: logAnalytics.outputs.resourceId
  }
}

/*
  An AI Foundry resources is a variant of a CognitiveServices/account resource type
*/
resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: 'ai-foundry-snippy'
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
    // required to work in AI Foundry
    allowProjectManagement: true
    // Defines developer API endpoint subdomain
    customSubDomainName: 'ai-foundry-snippy-${resourceToken}'
    disableLocalAuth: true
  }
}

/*
  Developer APIs are exposed via a project, which groups in- and outputs that relate to one use case, including files.
  Its advisable to create one project right away, so development teams can directly get started.
  Projects may be granted individual RBAC permissions and identities on top of what account provides.
*/
resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  name: 'snippy'
  parent: aiFoundry
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

/*
  Optionally deploy a model to use in playground, agents and other tools.
*/
resource modelDeployment_gpt4o 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: aiFoundry
  name: 'gpt-4o'
  sku: {
    capacity: 1
    name: 'GlobalStandard'
  }
  properties: {
    model: {
      name: 'gpt-4o'
      format: 'OpenAI'
    }
  }
}

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
  dependsOn:[
    modelDeployment_gpt4o
  ]
}

// Creates the Azure Foundry connection to your Azure App Insights resource
resource connection 'Microsoft.CognitiveServices/accounts/connections@2025-06-01' = {
  name: '${aiFoundry.name}-appinsights'
  parent: aiFoundry
  dependsOn: [
    aiFoundryAppInsightsContributor
    aiProjectAppInsightsContributor
  ]
  properties: {
    category: 'AppInsights'
    target: applicationInsights.outputs.resourceId
    authType: 'ApiKey'
    credentials: {
      key: applicationInsights.outputs.connectionString
    }
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: applicationInsights.outputs.resourceId
    }
  }
}

// RBAC: Grant AI Foundry access to Application Insights
resource aiFoundryAppInsightsContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(applicationInsights.name, aiFoundry.id, 'AppInsightsContributor')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'ae349356-3a1b-4a5e-921d-050484c6347e'
    ) // Application Insights Component Contributor
    principalId: aiFoundry.identity.principalId
    principalType: 'ServicePrincipal'
  }
  // make sure foundry operations are done
  dependsOn:[
    modelDeployment_embedding
  ]
}

// RBAC: Grant AI Project access to Application Insights
resource aiProjectAppInsightsContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(applicationInsights.name, aiProject.id, 'AppInsightsContributor')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'ae349356-3a1b-4a5e-921d-050484c6347e'
    ) // Application Insights Component Contributor
    principalId: aiProject.identity.principalId
    principalType: 'ServicePrincipal'
  }
  // make sure other operation is done
  dependsOn:[
    aiFoundryAppInsightsContributor
  ]  
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
    modelDeployment_gpt4o
  ]
}

output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output endpoints array = [
  'https://${functionApp.properties.defaultHostName}/api/health'
  'https://${functionApp.properties.defaultHostName}/api/snippets'
  'https://${functionApp.properties.defaultHostName}/api/orchestrators/embeddings'
  'https://${functionApp.properties.defaultHostName}/api/query'
]
output storageConnectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=<WILL_BE_SET>;EndpointSuffix=core.windows.net'
output storageAccountName string = storage.name

output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint
output cosmosDatabaseName string = cosmosDatabase.name
output cosmosContainerName string = cosmosContainer.name

output appInsightsConnectionString string = applicationInsights.outputs.connectionString

// something like this: https://ai-foundry-snippy-xswd3cnfrredy.services.ai.azure.com/api/projects/snippy
// openai: https://ai-foundry-snippy-xswd3cnfrredy.openai.azure.com/
output aiProjectConnectionString string = 'https://${aiFoundry.properties.customSubDomainName}.services.ai.azure.com/api/projects/${aiProject.name}'
output aiFoundryOpenAiEndpoint string = 'https://${aiFoundry.properties.customSubDomainName}.openai.azure.com'
