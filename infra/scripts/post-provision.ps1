# Get the Cosmos DB account name from the environment
$cosmosAccount = $env:COSMOS_ACCOUNT_NAME
$databaseName = $env:COSMOS_DATABASE_NAME
$containerName = $env:COSMOS_CONTAINER_NAME

# Create the vector index
az cosmosdb sql container create `
  --account-name $cosmosAccount `
  --database-name $databaseName `
  --name $containerName `
  --partition-key-path "/name" `
  --vector-embeddings '{
    "vectorEmbeddings": [{
      "path": "/embedding",
      "dataType": "int8",
      "dimensions": 1536,
      "distanceFunction": "cosine"
    }]
  }'

# Verify the container was created
az cosmosdb sql container show `
  --account-name $cosmosAccount `
  --database-name $databaseName `
  --name $containerName 