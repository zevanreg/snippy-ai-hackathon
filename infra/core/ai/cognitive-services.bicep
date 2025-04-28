@description('Azure region of the deployment')
param location string

@description('Tags to add to the resources')
param tags object

@description('AI services name')
param aiServicesName string

@description('The embedding model name to deploy')
param embeddingModelName string = 'text-embedding-3-small'

@description('The embedding model format')
param embeddingModelFormat string = 'OpenAI'

@description('The embedding model version')
param embeddingModelVersion string = '3'

@description('The embedding model SKU name')
param embeddingModelSkuName string = 'Standard'

@description('The embedding model capacity')
param embeddingModelCapacity int = 1

@description('The chat model name to deploy')
param chatModelName string = 'gpt-4o'

@description('The chat model format')
param chatModelFormat string = 'OpenAI'

@description('The chat model version')
param chatModelVersion string = '1106-preview'

@description('The chat model SKU name')
param chatModelSkuName string = 'Standard'

@description('The chat model capacity')
param chatModelCapacity int = 1

resource aiServices 'Microsoft.CognitiveServices/accounts@2024-06-01-preview' = {
  name: aiServicesName
  location: location
  tags: tags
  sku: {
    name: 'S0'
  }
  kind: 'OpenAI'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: toLower(aiServicesName)
    publicNetworkAccess: 'Enabled'
  }
}

resource embeddingModelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-06-01-preview' = {
  parent: aiServices
  name: embeddingModelName
  sku: {
    capacity: embeddingModelCapacity
    name: embeddingModelSkuName
  }
  properties: {
    model: {
      format: embeddingModelFormat
      name: embeddingModelName
      version: embeddingModelVersion
    }
  }
}

resource chatModelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-06-01-preview' = {
  parent: aiServices
  name: chatModelName
  sku: {
    name: chatModelSkuName
    capacity: chatModelCapacity
  }
  properties: {
    model: {
      format: chatModelFormat
      name: chatModelName
      version: chatModelVersion
    }
  }
}

output aiServicesName string = aiServices.name
output aiServicesId string = aiServices.id
output aiServicesEndpoint string = aiServices.properties.endpoint
output embeddingDeploymentName string = embeddingModelDeployment.name
output chatDeploymentName string = chatModelDeployment.name 
