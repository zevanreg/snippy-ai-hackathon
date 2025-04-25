@description('Azure region of the deployment')
param location string

@description('Tags to add to the resources')
param tags object

@description('Cosmos DB account name')
param accountName string

@description('Database name')
param databaseName string = 'snippy'

@description('Container name for snippets')
param containerName string = 'snippets'

@description('AI Services name')
param aiServicesName string

resource account 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: accountName
  location: location
  tags: tags
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
    enableFreeTier: false
  }
}

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  parent: account
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
  }
}

resource container 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: containerName
  properties: {
    resource: {
      id: containerName
      partitionKey: {
        paths: [
          '/name'
        ]
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
            path: '/"_etag"/?'
          }
        ]
      }
    }
  }
}

resource aiServices 'Microsoft.CognitiveServices/accounts@2024-06-01-preview' = {
  name: aiServicesName
  location: location
  tags: tags
}

resource embeddingModelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-06-01-preview' = {
  parent: aiServices
  name: 'embeddingModelDeployment'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'embeddingModelDeployment'
    }
  }
}

// Vector index needs to be created post-deployment via SDK or REST API
// as it's not yet supported in ARM/Bicep

output accountName string = account.name
output databaseName string = database.name
output containerName string = container.name
output documentEndpoint string = account.properties.documentEndpoint
output connectionString string = 'AccountEndpoint=${account.properties.documentEndpoint};AccountKey=${listKeys(account.id, account.apiVersion).primaryMasterKey}' 
