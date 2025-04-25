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
      {
        name: 'VectorSearch'
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
        vectorIndexes: [
          {
            path: '/embedding'
            kind: 'HNSW'
            dimensions: 1536
            similarity: 'cosine'
          }
        ]
      }
    }
  }
}

output accountName string = account.name
output databaseName string = database.name
output containerName string = container.name
output documentEndpoint string = account.properties.documentEndpoint
output connectionString string = 'AccountEndpoint=${account.properties.documentEndpoint};AccountKey=${account.listKeys().primaryMasterKey}' 