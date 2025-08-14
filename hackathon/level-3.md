# Level 3 — Vector Search + Q&A with Citations

Goal: Query endpoint that retrieves relevant snippets and composes an answer with citations.

## Tasks
- Add HTTP route `POST /query` accepting `{question, projectId}`.
- Use `agents/tools/vector_search.py` (or Cosmos `query_similar_snippets`) to get top-K.
- Call Azure OpenAI Chat (async) to compose grounded answer.
- Return `{answer, citations: [{id, score, title?}], usage}`.
- Retries/backoff and timeouts for external calls; config via env.

## Acceptance
- Deterministic response shape and proper error handling.
- All external calls async and mocked in tests.

## Testing
- `tests/test_query_pipeline.py` with `pytest-asyncio`.
- Mock vector search and chat; verify prompt and mapping.

## Env vars
- `VECTOR_TOP_K`, `OPENAI_CHAT_MODEL`, `OPENAI_TEMPERATURE`, `REQUEST_TIMEOUT_SEC`

---

## Deployment Options

### Option 1: Local Development
Ask a question and receive grounded answer with citations locally.

```powershell
$body = @{ projectId = "default-project"; question = "How do we save and retrieve snippets?" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:7071/api/query -ContentType application/json -Body $body
```

### Option 2: Cloud Deployment with AZD
```bash
# Deploy to Azure
azd auth login
azd up

# Test query endpoint in the cloud
$functionAppUrl = "https://your-function-app.azurewebsites.net"
$body = @{ projectId = "default-project"; question = "How do we save and retrieve snippets?" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$functionAppUrl/api/query" -ContentType application/json -Body $body
```

Benefits of cloud deployment:
- Real Azure OpenAI chat completions (no mocking)
- Real Cosmos DB vector search
- Production-like performance and behavior
