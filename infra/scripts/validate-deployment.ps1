# Get environment variables
$storageAccount = $env:STORAGE_ACCOUNT
$functionApp = $env:AZURE_FUNCTION_NAME

# 1. Test Storage access via MSI
Write-Host "Testing storage access via MSI..."
az storage blob list `
  --account-name $storageAccount `
  --container-name snippet-backups `
  --auth-mode login

# 2. Test Cosmos vector query
Write-Host "Testing Cosmos vector query..."
python -c @"
import os, asyncio, data.cosmos_ops as c
async def main():
    await c.query_similar_snippets([0]*1536, project_id='default-project')
asyncio.run(main())
"@

# 3. Make a smoke request
Write-Host "Making smoke request to Function App..."
$body = @{
    name = "hello"
    code = "print(123)"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "https://$functionApp.azurewebsites.net/api/snippets" `
  -Method Post `
  -Body $body `
  -ContentType "application/json" 