param location string
param resourceToken string
param tags object

// ==================================
// Level 1: Foundation Resources
// - Cosmos DB (Document storage only)
// - Function App (Basic HTTP API)
// - No AI services (DISABLE_OPENAI=1)
// ==================================

// Cosmos DB Account - Basic setup without vector search
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

// Cosmos DB Container - Basic indexing (no vector support yet)
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
      }
    }
  }
}

// Storage Account - Minimal setup for Function App
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

// Function App - Level 1 configuration
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

// ==================================
// Outputs
// ==================================
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint
output cosmosDatabaseName string = cosmosDatabase.name
output cosmosContainerName string = cosmosContainer.name
output storageAccountName string = storage.name
