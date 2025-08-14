param location string
param resourceToken string
param tags object

// Basic storage account for the function app
resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
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
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: 'cosmos-${resourceToken}'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
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
resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosAccount
  name: 'dev-snippet-db'
  properties: {
    resource: {
      id: 'dev-snippet-db'
    }
  }
}

// Cosmos DB Container with basic indexing (vector policy will be configured via code)
resource cosmosContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
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
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
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
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
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
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c') // Cosmos DB Built-in Data Contributor
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output endpoints array = [
  'https://${functionApp.properties.defaultHostName}/api/health'
  'https://${functionApp.properties.defaultHostName}/api/snippets'
  'https://${functionApp.properties.defaultHostName}/api/orchestrators/embeddings'
  'https://${functionApp.properties.defaultHostName}/api/query'
]
output storageConnectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=<WILL_BE_SET>;EndpointSuffix=core.windows.net'
output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint
output cosmosDatabaseName string = cosmosDatabase.name
output cosmosContainerName string = cosmosContainer.name
