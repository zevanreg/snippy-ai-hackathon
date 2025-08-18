param location string
param resourceToken string
param tags object

// ==================================
// Complete Platform Resources
// - Cosmos DB with vector search
// - Function App with full AI capabilities  
// - Azure AI Foundry (OpenAI services)
// - Storage with blob containers
// - Key Vault for security
// ==================================

// Cosmos DB Account - Basic setup, enhanced for vector search in level 2+
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

// Cosmos DB Container with vector indexing enabled
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

// Vector-enabled container 
resource cosmosVectorContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-04-15' = {
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

// Storage Account
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

resource storageServices 'Microsoft.Storage/storageAccounts/blobServices@2025-01-01' = {
  parent: storage
  name: 'default'
}

// Blob containers
resource snippetInputsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2025-01-01' = {
  name: 'snippet-inputs'
  parent: storageServices
}

resource snippetBackupsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2025-01-01' = {
  name: 'snippet-backups'
  parent: storageServices
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

// ==================================
// AI Services
// ==================================

// Log Analytics Workspace for Application Insights
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-${resourceToken}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
  tags: tags
}

// Application Insights
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appins-${resourceToken}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
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
  }
  tags: tags
}

// Embedding model deployment
resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: aiFoundry
  name: 'text-embedding-3-small'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-small'
      version: '1'
    }
  }
  sku: {
    name: 'Standard'
    capacity: 120
  }
}

// Chat model deployment
resource chatDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: aiFoundry
  name: 'gpt-4o'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-08-06'
    }
  }
  sku: {
    name: 'Standard'
    capacity: 10
  }
  dependsOn: [embeddingDeployment]
}

// ==================================
// Security
// ==================================

// Key Vault for secure credential storage
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv-snippy-${resourceToken}'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: tenant().tenantId
    enabledForDeployment: false
    enabledForTemplateDeployment: false
    enabledForDiskEncryption: false
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    accessPolicies: []
  }
  tags: tags
}

// ==================================
// Function App (with conditional app settings)
// ==================================

// Function App with level-appropriate configuration
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
          name: 'DISABLE_OPENAI'
          value: '0'
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

// ==================================
// RBAC Assignments
// ==================================

// Grant Function App access to Cosmos DB
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

// Grant Function App access to AI Foundry
resource aiFoundryContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiFoundry.id, functionApp.id, 'CognitiveServicesUser')
  scope: aiFoundry
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'a97b65f3-24c7-4388-baec-2e87135dc908'
    ) // Cognitive Services User
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Grant Function App access to Storage
resource storageContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, functionApp.id, 'StorageBlobDataContributor')
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    ) // Storage Blob Data Contributor
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Grant Function App access to Key Vault
resource keyVaultSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, functionApp.id, 'KeyVaultSecretsUser')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69e6'
    ) // Key Vault Secrets User
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ==================================
// Outputs
// ==================================

// Core outputs (always available)
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint
output cosmosDatabaseName string = cosmosDatabase.name
output cosmosContainerName string = cosmosContainer.name
output storageAccountName string = storage.name

// AI outputs - use calculated values instead of resource references
output aiProjectConnectionString string = 'https://ai-foundry-snippy-${resourceToken}.openai.azure.com/'
output aiFoundryProjectName string = 'ai-foundry-snippy-${resourceToken}'
output aiFoundryOpenAiEndpoint string = 'https://ai-foundry-snippy-${resourceToken}.openai.azure.com/'
output embeddingModelDeploymentName string = 'text-embedding-3-small'
output appInsightsConnectionString string = applicationInsights.properties.ConnectionString

// Chat outputs
output chatModelDeploymentName string = 'gpt-4o'
output chatModelDeploymentType string = 'gpt-4o'

// Storage outputs
output storageBlobContainerSnippetInputs string = 'snippet-inputs'
output storageBlobContainerSnippetBackups string = 'snippet-backups'

// Security outputs - use calculated values
output keyVaultUrl string = 'https://kv-snippy-${resourceToken}.vault.azure.net/'
output managedIdentityClientId string = functionApp.identity.principalId
