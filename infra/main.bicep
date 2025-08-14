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
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName, project: 'snippy-ai-hackathon' }

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: 'snippy-ai-hackathon'
  location: location
  tags: tags
}

module hackathonResources 'hackathon-resources.bicep' = {
  name: 'hackathonResources'
  scope: rg
  params: {
    location: location
    resourceToken: resourceToken
    tags: tags
  }
}

// // Deploy resources using a module in the resource group scope
// module resources 'simple-resources.bicep' = {
//   name: 'simpleResources'
//   scope: rg
//   params: {
//     location: location
//     resourceToken: resourceToken
//     tags: tags
//   }
// }

// // Output the Function App URL
// output REACT_APP_API_BASE_URL string = resources.outputs.functionAppUrl
// output SERVICE_API_ENDPOINTS array = resources.outputs.endpoints
// output AZUREWEBJOBSSTORAGE string = resources.outputs.storageConnectionString


// // ==================================
// // Outputs
// // ==================================
// // Define outputs needed specifically for configuring local.settings.json
// // Use 'azd env get-values' to retrieve these after provisioning.
// // WARNING: Secrets (Keys, Connection Strings) are output directly and will be visible in deployment history.
// // Output names directly match the corresponding keys in local.settings.json for easier mapping.

// @description('Cosmos DB endpoint. Output name matches the COSMOS_ENDPOINT key in local settings.')
// output COSMOS_ENDPOINT string = cosmosDb.outputs.documentEndpoint

// @description('Connection string for the Azure AI Project. Output name matches the PROJECT_CONNECTION_STRING key in local settings.')
// output PROJECT_CONNECTION_STRING string = aiProject.outputs.projectConnectionString

// @description('Endpoint for Azure OpenAI services. Output name matches the AZURE_OPENAI_ENDPOINT key in local settings.')
// output AZURE_OPENAI_ENDPOINT string = openai.outputs.azureOpenAIServiceEndpoint

// @description('Primary key for Azure OpenAI services. Output name matches the AZURE_OPENAI_KEY key in local settings.')
// // @secure() - issue with latest bicep version, set secure in cognitive services module
// output AZURE_OPENAI_KEY string = openai.outputs.primaryKey

// @description('Name of the deployed Azure Function App.')
// output AZURE_FUNCTION_NAME string = api.outputs.SERVICE_API_NAME // Function App Name

// @description('Connection string for the Azure Storage Account. Output name matches the AzureWebJobsStorage key in local settings.')
// output AZUREWEBJOBSSTORAGE string = storage.outputs.primaryBlobEndpoint
