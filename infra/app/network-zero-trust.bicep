@description('Azure region of the deployment')
param location string

@description('Tags to add to the resources')
param tags object

@description('Cosmos DB account name')
param cosmosAccountName string

@description('Storage account resource ID')
param storageAccountId string

@description('Key Vault resource ID')
param keyVaultId string

@description('Private DNS zone name for Cosmos DB (documents)')
param privateDnsZoneDocuments string = 'privatelink.documents.azure.com'

@description('Private DNS zone name for Blob Storage')
param privateDnsZoneBlob string

@description('Private DNS zone name for Key Vault')
param privateDnsZoneKeyVault string

// VNet with two subnets: functions integration and private endpoints
resource vnet 'Microsoft.Network/virtualNetworks@2023-09-01' = {
  name: 'vnet-zero-${uniqueString(resourceGroup().id)}'
  location: location
  tags: tags
  properties: {
    addressSpace: { addressPrefixes: ['10.10.0.0/16'] }
    subnets: [
      {
        name: 'functions'
        properties: { addressPrefix: '10.10.1.0/24' }
      }
      {
        name: 'private-endpoints'
        properties: { addressPrefix: '10.10.2.0/24' }
      }
    ]
  }
}

// Private DNS zones
resource pdnsCosmos 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateDnsZoneDocuments
  location: 'global'
}
resource pdnsBlob 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateDnsZoneBlob
  location: 'global'
}
resource pdnsVault 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateDnsZoneKeyVault
  location: 'global'
}

// VNet links
resource vnetLink1 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  name: 'pdns-cosmos-link'
  parent: pdnsCosmos
  location: 'global'
  properties: { registrationEnabled: false, virtualNetwork: { id: vnet.id } }
}
resource vnetLink2 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  name: 'pdns-blob-link'
  parent: pdnsBlob
  location: 'global'
  properties: { registrationEnabled: false, virtualNetwork: { id: vnet.id } }
}
resource vnetLink3 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  name: 'pdns-kv-link'
  parent: pdnsVault
  location: 'global'
  properties: { registrationEnabled: false, virtualNetwork: { id: vnet.id } }
}

// Private endpoint for Cosmos (SQL)
resource peCosmos 'Microsoft.Network/privateEndpoints@2023-05-01' = {
  name: 'pep-cosmos-${uniqueString(resourceGroup().id)}'
  location: location
  properties: {
    subnet: { id: resourceId('Microsoft.Network/virtualNetworks/subnets', vnet.name, 'private-endpoints') }
    privateLinkServiceConnections: [{
      name: 'cosmos'
      properties: {
        privateLinkServiceId: resourceId('Microsoft.DocumentDB/databaseAccounts', cosmosAccountName)
        groupIds: ['Sql']
      }
    }]
  }
}
resource peCosmosDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2020-05-01' = {
  name: 'cosmos-dns'
  parent: peCosmos
  properties: { privateDnsZoneConfigs: [{ name: 'cfg', properties: { privateDnsZoneId: pdnsCosmos.id } }] }
}

// Private endpoint for Storage (blob)
resource peBlob 'Microsoft.Network/privateEndpoints@2023-05-01' = {
  name: 'pep-stg-${uniqueString(resourceGroup().id)}'
  location: location
  properties: {
    subnet: { id: resourceId('Microsoft.Network/virtualNetworks/subnets', vnet.name, 'private-endpoints') }
    privateLinkServiceConnections: [{
      name: 'blob'
      properties: {
        privateLinkServiceId: storageAccountId
        groupIds: ['blob']
      }
    }]
  }
}
resource peBlobDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2020-05-01' = {
  name: 'blob-dns'
  parent: peBlob
  properties: { privateDnsZoneConfigs: [{ name: 'cfg', properties: { privateDnsZoneId: pdnsBlob.id } }] }
}

// Private endpoint for Key Vault
resource peKv 'Microsoft.Network/privateEndpoints@2023-05-01' = {
  name: 'pep-kv-${uniqueString(resourceGroup().id)}'
  location: location
  properties: {
    subnet: { id: resourceId('Microsoft.Network/virtualNetworks/subnets', vnet.name, 'private-endpoints') }
    privateLinkServiceConnections: [{
      name: 'vault'
      properties: {
        privateLinkServiceId: keyVaultId
        groupIds: ['vault']
      }
    }]
  }
}
resource peKvDns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2020-05-01' = {
  name: 'kv-dns'
  parent: peKv
  properties: { privateDnsZoneConfigs: [{ name: 'cfg', properties: { privateDnsZoneId: pdnsVault.id } }] }
}

output vnetId string = vnet.id
output functionsSubnetId string = resourceId('Microsoft.Network/virtualNetworks/subnets', vnet.name, 'functions')
