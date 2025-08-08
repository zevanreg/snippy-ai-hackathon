# Level 2 — Durable Orchestration: Fan-out Embeddings

Goal: Orchestrate chunking and embeddings via Durable Functions.

## Tasks
- Create blueprint `bp_embeddings` with:
  - Orchestrator (sync `def`) that:
    - Receives `{projectId, name, text}`
    - Splits text into chunks (size from env `CHUNK_SIZE`, default 800)
    - Fans-out activity calls to embed each chunk via `yield context.task_all([...])`
    - Aggregates results and writes to Cosmos via `data/cosmos_ops.py`
  - Activity (`async def`) that calls Azure OpenAI Embeddings (async) or returns mock if `DISABLE_OPENAI=1`.
- Add HTTP starter route that starts the orchestration and returns `create_check_status_response()`.
- Register blueprint with `app.register_blueprint(bp_embeddings)` in `function_app.py`.

## Acceptance
- Orchestrator yields on tasks and returns aggregated JSON.
- Activities are async and return JSON-serialisable data.
- Logging at start, per-chunk, and aggregate steps.

## Hints
- Keep network calls out of orchestrator; only in activities.
- Chunk deterministically; keep tests small.

## Testing
- `tests/test_orchestrator_embeddings.py` with `pytest-asyncio`.
- Use `AsyncMock` for OpenAI client; cover error and success branches.

## Env vars
- `CHUNK_SIZE`, `OPENAI_EMBED_MODEL`, `DISABLE_OPENAI`

---

## Quickstart (local)
Start the orchestration and check status URLs.

```powershell
$body = @{ projectId = "default-project"; name = "hello.txt"; text = "Hello world" } | ConvertTo-Json
$r = Invoke-WebRequest -Method Post -Uri http://localhost:7071/api/orchestrators/embeddings -ContentType application/json -Body $body
$r.StatusCode  # expected 202
$r.Headers["Location"]  # status endpoint
```
