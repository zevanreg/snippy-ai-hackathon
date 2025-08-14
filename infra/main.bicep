targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
@allowed(['eastus', 'eastus2', 'westus', 'westus2', 'westus3'])
@metadata({
  azd: {
    type: 'location'
  }
})
param location string

// Use simplified approach for Level 1
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: 'snippy-ai-hackathon'
  location: location
  tags: tags
}

// Deploy resources using a module in the resource group scope
module resources 'simple-resources.bicep' = {
  name: 'simpleResources'
  scope: rg
  params: {
    location: location
    resourceToken: resourceToken
    tags: tags
  }
}

// Output the Function App URL
output REACT_APP_API_BASE_URL string = resources.outputs.functionAppUrl
output SERVICE_API_ENDPOINTS array = resources.outputs.endpoints
output AZUREWEBJOBSSTORAGE string = resources.outputs.storageConnectionString
