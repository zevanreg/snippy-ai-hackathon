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

// Blob service for storage account
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storage
  name: 'default'
}

// Blob container for code snippets
resource blobContainer_snippetBackups 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'snippet-backups'
  properties: {
    publicAccess: 'None'
  }
}

resource blobContainer_snippetInputs 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'snippet-inputs'
  properties: {
    publicAccess: 'None'
  }
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
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: applicationInsights.properties.InstrumentationKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: applicationInsights.properties.ConnectionString
        }
        {
          name: 'PYTHON_ENABLE_WORKER_EXTENSIONS'
          value: 'True'
        }
        {
          name: 'COSMOS_ENDPOINT'
          value: cosmosAccount.properties.documentEndpoint
        }
        {
          name: 'COSMOS_DATABASE_NAME'
          value: cosmosDatabase.name
        }
        {
          name: 'COSMOS_CONTAINER_NAME'
          value: cosmosContainer.name
        }
        {
          name: 'COSMOS_VECTOR_TOP_K'
          value: '30'
        }
        {
          name: 'COSMOS_KEY'
          value: cosmosAccount.listKeys().primaryMasterKey
        }
        {
          name: 'BLOB_CONTAINER_NAME'
          value: blobContainer_snippetBackups.name
        }
        {
          name: 'EMBEDDING_MODEL_DEPLOYMENT_NAME'
          value: modelDeployment_embedding.name
        }
        {
          name: 'AGENTS_MODEL_DEPLOYMENT_NAME'
          value: modelDeployment_chat.name
        }
        {
          name: 'PROJECT_CONNECTION_STRING'
          value: 'https://${aiFoundry.properties.customSubDomainName}.services.ai.azure.com/api/projects/${aiProject.name}'
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: 'https://${aiFoundry.properties.customSubDomainName}.openai.azure.com'
        }
        {
          name: 'AZURE_OPENAI_KEY'
          value: aiFoundry.listKeys().key1
        }
        {
          name: 'VECTOR_TOP_K'
          value: '5'
        }
        {
          name: 'OPENAI_TEMPERATURE'
          value: '0.2'
        }
        {
          name: 'REQUEST_TIMEOUT_SEC'
          value: '20'
        }
        {
          name: 'CHUNK_SIZE'
          value: '800'
        }
        {
          name: 'INGESTION_CONTAINER'
          value: blobContainer_snippetInputs.name
        }
        {
          name: 'MAX_BLOB_MB'
          value: '2'
        }
        {
          name: 'DEFAULT_PROJECT_ID'
          value: 'default-project'
        }
        {
          name: 'OPENAI_CHAT_MODEL'
          value: modelDeployment_chat.name
        }
        {
          name: 'MAX_AGENT_ITERATIONS'
          value: '3'
        }
        {
          name: 'AGENT_TOKEN_LIMIT'
          value: '4000'
        }
        {
          name: 'ENABLE_CONTENT_FILTER'
          value: '0'
        }
        {
          name: 'MAX_CONCURRENT_AGENTS'
          value: '3'
        }
      ]
      cors: {
        allowedOrigins: ['*']
        supportCredentials: false
      }
    }
  }
  tags: union(tags, {
    'azd-service-name': 'api'
  })
}
module logAnalytics 'br/public:avm/res/operational-insights/workspace:0.7.0' = {
  name: 'loganalytics'
  params: {
    name: 'log-${resourceToken}'
    location: location
    tags: tags
  }
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appins-${resourceToken}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.outputs.resourceId
  }
}

/*
  An AI Foundry resources is a variant of a CognitiveServices/account resource type
*/
resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
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
    disableLocalAuth: false
  }
  tags: tags
}

/*
  Developer APIs are exposed via a project, which groups in- and outputs that relate to one use case, including files.
  Its advisable to create one project right away, so development teams can directly get started.
  Projects may be granted individual RBAC permissions and identities on top of what account provides.
*/
resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  name: 'snippy'
  parent: aiFoundry
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {    
  }
  tags: tags
}

/*
  Optionally deploy a model to use in playground, agents and other tools.
*/
resource modelDeployment_chat 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
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
    modelDeployment_chat
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
    target: applicationInsights.id
    authType: 'ApiKey'
    credentials: {
      key: applicationInsights.properties.ConnectionString
    }
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: applicationInsights.id
    }
  }
}


// RBAC Assignments

var monitoringMetricsPublisherId = '3913510d-42f4-4e42-8a64-420c390055eb'

resource roleAssignmentAppInsights 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, applicationInsights.id, functionApp.id, monitoringMetricsPublisherId)
  scope: applicationInsights
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringMetricsPublisherId)
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
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
    modelDeployment_chat
  ]
}




output storageAccountName string = storage.name
output storageConnectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
output storageBlobContainerSnippetInputs string = blobContainer_snippetInputs.name
output storageBlobContainerSnippetBackups string = blobContainer_snippetBackups.name

output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint
output cosmosKey string = cosmosAccount.listKeys().primaryMasterKey
output cosmosDatabaseName string = cosmosDatabase.name
output cosmosContainerName string = cosmosContainer.name


output aiProjectConnectionString string = 'https://${aiFoundry.properties.customSubDomainName}.services.ai.azure.com/api/projects/${aiProject.name}'
output aiFoundryProjectName string = aiProject.name
output aiFoundryOpenAiEndpoint string = 'https://${aiFoundry.properties.customSubDomainName}.openai.azure.com'
output aiFoundryOpenAiKey string = aiFoundry.listKeys().key1
output embeddingModelDeploymentName string = modelDeployment_embedding.name
output chatModelDeploymentName string = modelDeployment_chat.name
output chatModelDeploymentType string = modelDeployment_chat.properties.model.name


output functionAppName string = functionApp.name
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output endpoints array = [
  'https://${functionApp.properties.defaultHostName}/api/health'
  'https://${functionApp.properties.defaultHostName}/api/snippets'
  'https://${functionApp.properties.defaultHostName}/api/orchestrators/embeddings'
  'https://${functionApp.properties.defaultHostName}/api/query'
]

output appInsightsConnectionString string = applicationInsights.properties.ConnectionString

