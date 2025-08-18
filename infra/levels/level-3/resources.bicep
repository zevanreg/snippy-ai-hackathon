param resourceToken string
param functionAppName string
param aiFoundryName string

// ==================================
// Level 3: Chat Completion Addition
// - Chat model deployment (GPT-4o)
// - Enhanced query capabilities
// ==================================

// Reference existing Function App to update settings
resource functionApp 'Microsoft.Web/sites@2024-11-01' existing = {
  name: functionAppName
}

// Reference existing AI Foundry
resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: aiFoundryName
}

// Chat model deployment
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

// Update Function App settings to include chat model
resource functionAppSettings 'Microsoft.Web/sites/config@2024-11-01' = {
  parent: functionApp
  name: 'appsettings'
  properties: {
    FUNCTIONS_WORKER_RUNTIME: 'python'
    FUNCTIONS_EXTENSION_VERSION: '~4'
    AzureWebJobsStorage: functionApp.listkeys().keys[0].value
    PYTHON_ENABLE_WORKER_EXTENSIONS: 'True'
    DISABLE_OPENAI: '0'
    COSMOS_ENDPOINT: reference(resourceId('Microsoft.DocumentDB/databaseAccounts', 'cosmos-${resourceToken}')).documentEndpoint
    COSMOS_DATABASE_NAME: 'dev-snippet-db'
    COSMOS_CONTAINER_NAME: 'code-snippets-vectors'
    COSMOS_VECTOR_TOP_K: '5'
    CHUNK_SIZE: '800'
    APPINSIGHTS_INSTRUMENTATIONKEY: reference(resourceId('Microsoft.Insights/components', 'appins-${resourceToken}')).InstrumentationKey
    APPLICATIONINSIGHTS_CONNECTION_STRING: reference(resourceId('Microsoft.Insights/components', 'appins-${resourceToken}')).ConnectionString
    AI_PROJECT_CONNECTION_STRING: 'https://${aiFoundry.properties.customSubDomainName}.services.ai.azure.com/api/projects/snippy'
    AI_FOUNDRY_OPENAI_ENDPOINT: 'https://${aiFoundry.properties.customSubDomainName}.openai.azure.com'
    EMBEDDING_MODEL_DEPLOYMENT_NAME: 'text-embedding-3-small'
    CHAT_MODEL_DEPLOYMENT_NAME: modelDeployment_chat.name
    CHAT_MODEL_DEPLOYMENT_TYPE: modelDeployment_chat.properties.model.name
  }
}

// ==================================
// Outputs
// ==================================
output chatModelDeploymentName string = modelDeployment_chat.name
output chatModelDeploymentType string = modelDeployment_chat.properties.model.name
