param location string
param resourceToken string
param tags object
param functionAppName string

// ==================================
// Level 6: Zero Trust Security
// - Azure Key Vault for secure credential storage
// - Enhanced managed identity configuration
// - Security monitoring and compliance
// ==================================

// Reference existing Function App
resource functionApp 'Microsoft.Web/sites@2024-11-01' existing = {
  name: functionAppName
}

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

// Update Function App with Key Vault reference patterns
resource functionAppSettings 'Microsoft.Web/sites/config@2024-11-01' = {
  parent: functionApp
  name: 'appsettings'
  properties: {
    // Core Function App settings
    FUNCTIONS_WORKER_RUNTIME: 'python'
    FUNCTIONS_EXTENSION_VERSION: '~4'
    PYTHON_ENABLE_WORKER_EXTENSIONS: 'True'
    DISABLE_OPENAI: '0'
    
    // Key Vault integration (Level 6 security enhancement)
    KEY_VAULT_URL: keyVault.properties.vaultUri
    AZURE_KEY_VAULT_ENABLED: 'true'
    
    // Security settings
    ENABLE_ZERO_TRUST_SECURITY: 'true'
    REQUIRE_AUTHENTICATION: 'true'
    AUDIT_LOGGING_ENABLED: 'true'
    
    // Placeholder settings - these would reference Key Vault secrets in production
    COSMOS_ENDPOINT: '@Microsoft.KeyVault(VaultName=${keyVault.name};SecretName=cosmos-endpoint)'
    COSMOS_DATABASE_NAME: 'dev-snippet-db'
    COSMOS_CONTAINER_NAME: 'code-snippets-vectors'
    COSMOS_VECTOR_TOP_K: '5'
    CHUNK_SIZE: '800'
    
    // AI settings - would be stored in Key Vault in production
    AI_PROJECT_CONNECTION_STRING: '@Microsoft.KeyVault(VaultName=${keyVault.name};SecretName=ai-project-connection-string)'
    AI_FOUNDRY_OPENAI_ENDPOINT: '@Microsoft.KeyVault(VaultName=${keyVault.name};SecretName=ai-foundry-openai-endpoint)'
    EMBEDDING_MODEL_DEPLOYMENT_NAME: 'text-embedding-3-small'
    CHAT_MODEL_DEPLOYMENT_NAME: 'gpt-4o'
    CHAT_MODEL_DEPLOYMENT_TYPE: 'gpt-4o'
    
    // Application Insights
    APPLICATIONINSIGHTS_CONNECTION_STRING: '@Microsoft.KeyVault(VaultName=${keyVault.name};SecretName=app-insights-connection-string)'
    
    // Multi-agent settings
    DURABLE_FUNCTION_HUB_NAME: 'snippy-multi-agent'
    MULTI_AGENT_MAX_CONCURRENT_TASKS: '10'
    MULTI_AGENT_TIMEOUT_MINUTES: '30'
    ENABLE_MULTI_AGENT_ORCHESTRATION: 'true'
    DEEP_WIKI_AGENT_ENABLED: 'true'
    CODE_STYLE_AGENT_ENABLED: 'true'
  }
}

// ==================================
// Outputs
// ==================================
output keyVaultUrl string = keyVault.properties.vaultUri
output managedIdentityClientId string = functionApp.identity.principalId
