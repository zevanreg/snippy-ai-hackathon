# Quickstart — Local Ingestion, Observability, and Ops

This quickstart extracts the Level 4 operational steps so you can run the blob-trigger ingestion locally, observe telemetry, and troubleshoot.

See the full challenge details in `hackathon/level-4.md`.

## Quickstart (local)
Pre-reqs:
- Azurite (VS Code extension) or Azure Storage account. For local dev, keep `AzureWebJobsStorage=UseDevelopmentStorage=true`.
- Container name in env `INGESTION_CONTAINER` (default `snippet-input`).

Steps (Windows PowerShell + Azure CLI):
1) Ensure container exists

    ```powershell
    az storage container create --name snippet-input --connection-string UseDevelopmentStorage=true
    ```

2) Create a small test file and upload it

    ```powershell
    Set-Content -Path .\sample.md -Value "# Hello\nThis is a tiny doc to ingest."
    az storage blob upload --file .\sample.md --container-name snippet-input --name sample.md --connection-string UseDevelopmentStorage=true --overwrite
    ```

3) Observe function logs
- The trigger should log: "Ingestion started orchestration id=... for sample.md".
- The Durable orchestration should fan-out embeddings and persist to Cosmos.

4) Verify durable instance (optional)
- Check the Functions console output for instanceId lines.
- For HTTP-driven orchestrations you’d poll the status URL; for blob-driven, use logs/App Insights.

Tip: To run without external AI calls, set `DISABLE_OPENAI=1` in `src/local.settings.json`.

## Observability
- Set `APPINSIGHTS_CONNECTION_STRING` in `src/local.settings.json` to send telemetry to Application Insights.
- Useful KQL (in Application Insights → Logs):

    ```kusto
    traces
    | where timestamp > ago(1h)
    | where message has "Ingestion started orchestration"
    | project timestamp, severityLevel, message
    | order by timestamp desc
    ```

- Add custom metrics/events in your implementation (e.g., items processed, chunk count, durations, failures).

## RBAC (cloud deployment)
- Storage trigger access: assign Managed Identity of the Function App the role "Storage Blob Data Contributor" on the storage account hosting the container.
- Cosmos access: assign "Cosmos DB Built-in Data Contributor" (or scoped Data Plane role) on the target database/account.
- Ensure networking/firewall allows Function App to reach Storage and Cosmos.

## Resilience patterns
- Use size guard `MAX_BLOB_MB` to skip large files.
- Implement retries with exponential backoff for embedding calls and persistence.
- Optional circuit breaker: environment flag to early-exit on repeated failures.

## Troubleshooting
- No trigger on upload (local): ensure Azurite is running and container name matches `INGESTION_CONTAINER`.
- Unicode issues: ensure `blob.read().decode('utf-8', errors='ignore')` or equivalent.
- Cosmos errors: verify `COSMOS_ENDPOINT`, DB and container names, and identity/keys.
