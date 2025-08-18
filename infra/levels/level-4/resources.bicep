param functionAppName string
param storageAccountName string

// ==================================
// Level 4: Blob Storage Triggers & Enhanced Monitoring
// - Blob containers for file ingestion
// - Enhanced monitoring and observability
// ==================================

// Reference existing Function App
resource functionApp 'Microsoft.Web/sites@2024-11-01' existing = {
  name: functionAppName
}

// Reference existing Storage Account
resource storage 'Microsoft.Storage/storageAccounts@2025-01-01' existing = {
  name: storageAccountName
}

// Blob service for storage account
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storage
  name: 'default'
}

// Blob containers for Level 4
resource blobContainer_snippetInputs 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'snippet-inputs'
  properties: {
    publicAccess: 'None'
  }
}

resource blobContainer_snippetBackups 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'snippet-backups'
  properties: {
    publicAccess: 'None'
  }
}

// Grant Function App additional blob permissions
resource storageDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
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

// ==================================
// Outputs
// ==================================
output storageBlobContainerSnippetInputs string = blobContainer_snippetInputs.name
output storageBlobContainerSnippetBackups string = blobContainer_snippetBackups.name
