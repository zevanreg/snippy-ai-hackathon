# Quickstart — Local Development, Observability, and Advanced Features

This quickstart covers Level 4 operational steps (blob-trigger ingestion, telemetry) plus guidance for Levels 5-6 (multi-agent orchestration and zero trust security).

See the full challenge details in respective level files: `level-4.md`, `level-5.md`, `level-6.md`.

## Core Platform Quickstart (Levels 1-4)
Pre-reqs:
- Azure Storage account deployed via infrastructure templates
- Container name in env `INGESTION_CONTAINER` (default `snippet-input`).

Steps (Windows PowerShell + Azure CLI):
1) Ensure container exists

    ```powershell
    az storage container create --name snippet-input --account-name <your-storage-account>
    ```

2) Create a small test file and upload it

    ```powershell
    Set-Content -Path .\sample.md -Value "# Hello\nThis is a tiny doc to ingest."
    az storage blob upload --file .\sample.md --container-name snippet-input --name sample.md --account-name <your-storage-account> --overwrite
    ```

3) Observe function logs
- The trigger should log: "Ingestion started orchestration id=... for sample.md".
- The Durable orchestration should fan-out embeddings and persist to Cosmos.

4) Verify durable instance (optional)
- Check the Functions console output for instanceId lines.
- For HTTP-driven orchestrations you’d poll the status URL; for blob-driven, use logs/App Insights.

Note: All AI services are configured via Azure infrastructure - no local settings required.

## Observability
- Application Insights telemetry is configured automatically via the Azure infrastructure deployment.
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
- No trigger on upload: ensure container name matches `INGESTION_CONTAINER` and Azure Storage connection is configured.
- Unicode issues: ensure `blob.read().decode('utf-8', errors='ignore')` or equivalent.
- Cosmos errors: verify `COSMOS_ENDPOINT`, DB and container names, and identity/keys.

## Advanced Features Quickstart (Levels 5-6)

### Level 5: Multi-Agent Orchestration
Test multi-agent workflows locally:

```bash
# Deploy to Azure first
azd up

# Start multi-agent code review workflow
POST https://your-function-app.azurewebsites.net/api/orchestrators/multi-agent-review
{
  "projectId": "default-project",
  "snippetId": "example.py",
  "workflow": "code-review-and-docs"
}
```

Key environment variables for Level 5:
- `MAX_AGENT_ITERATIONS=10`
- `AGENT_TOKEN_LIMIT=50000`
- `ENABLE_CONTENT_FILTER=true`
- `AGENT_COMMUNICATION_TIMEOUT=300`
- `MAX_CONCURRENT_AGENTS=5`

### Level 6: Zero Trust Security
Deploy with Zero Trust configuration:

```bash
# Deploy with Zero Trust configuration
azd env set ZERO_TRUST_MODE true
azd env set NETWORK_ISOLATION true
azd env set PRIVATE_ENDPOINTS_ONLY true
azd up
```

Security validation checklist:
- ✅ All service-to-service communication uses private endpoints
- ✅ No public internet access from Function App (egress lockdown)
- ✅ All authentication uses Managed Identity (no secrets/keys)
- ✅ Network traffic is fully monitored and logged
- ✅ Security posture meets enterprise compliance standards

### Testing Advanced Features
Run comprehensive tests for all levels:

```bash
# Test Levels 1-4 (core functionality)
python -m pytest tests/test_level1_endpoints.py -v
python -m pytest tests/test_orchestrator_embeddings.py -v
python -m pytest tests/test_query_pipeline.py -v

# Test Level 5 (multi-agent)
python -m pytest tests/test_multi_agent_orchestration.py -v

# Test Level 6 (zero trust)
python -m pytest tests/test_zero_trust_security.py -v
```
