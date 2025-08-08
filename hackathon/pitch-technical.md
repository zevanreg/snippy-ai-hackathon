# Technical Pitch — Snippy AI Hackathon

Audience: Tech leads, staff/principal engineers, solution architects

Purpose: Validate an Azure-native reference for AI-grounded knowledge APIs built on serverless primitives with production-ready patterns (durability, observability, RBAC, cost-awareness).

---

## What we build (reference outcome)
- An Azure Functions (Python v2, blueprint) backend that:
  - Ingests short docs/snippets (HTTP + Blob trigger)
  - Fans-out to async embedding activities via Durable Functions
  - Stores metadata + vectors in Cosmos DB (DiskANN vector index)
  - Answers questions via vector search + Azure OpenAI chat with citations
  - Emits telemetry to Application Insights (logs, events, metrics)

## Architecture (incremental)
- Compute: Azure Functions
  - HTTP triggers: /snippets, /query, durable starter
  - Blob trigger: ingestion container
  - Durable Functions: orchestrator (sync def) + async activities
- Data: Cosmos DB (Core/SQL) with vectorEmbeddingPolicy on /embedding (DiskANN, cosine)
- AI: Azure AI Projects + Inference (embeddings, chat) with async clients
- Storage: Azure Storage account (ingestion container, Azurite for local)
- Observability: Application Insights (traces, customEvents, metrics)
- Identity: Managed Identity (Storage/Cosmos RBAC)

## Key technical patterns
- Durable fan-out/fan-in: orchestrator yields `context.task_all([...])`; all I/O in activities
- Async-first SDK usage: `azure-identity.aio`, `azure-ai-projects.aio`, Cosmos async client
- Config via env only; no secrets in code; Python 3.11, logging at INFO
- Blueprint model: single `app = func.FunctionApp()` and `app.register_blueprint(bp)`

## API surface (Level 1 & 3)
- POST /snippets → save snippet with embedding (HTTP + embeddings_input decorator)
- GET /snippets/{name} → retrieve by id
- POST /query {question, projectId} → answer + citations [{id, score}]
- POST /orchestrators/embeddings → starts durable instance (202 + status URLs)

## Data model (Cosmos)
- Container: `code-snippets`
- Partition key: `/name` (can evolve to `/projectId`)
- Doc fields: `{ id, name, projectId, code, type: 'code-snippet', embedding }`
- Vector index: int8/float vectors on `/embedding`, cosine distance (DiskANN)

## Environments & config (excerpt)
- Storage: `AzureWebJobsStorage`
- Cosmos: `COSMOS_ENDPOINT`, `COSMOS_DATABASE_NAME`, `COSMOS_CONTAINER_NAME`, `COSMOS_VECTOR_TOP_K`
- AI: `PROJECT_CONNECTION_STRING`, `EMBEDDING_MODEL_DEPLOYMENT_NAME`, `AGENTS_MODEL_DEPLOYMENT_NAME`, `DISABLE_OPENAI`
- Orchestration: `CHUNK_SIZE`, `VECTOR_TOP_K`, `REQUEST_TIMEOUT_SEC`
- Ingestion: `INGESTION_CONTAINER`, `MAX_BLOB_MB`, `DEFAULT_PROJECT_ID`
- Observability: `APPINSIGHTS_CONNECTION_STRING`

## Security & RBAC
- Managed Identity for Function App
  - Storage: Storage Blob Data Contributor
  - Cosmos: Built-in Data Contributor (or data plane role)
- Secrets: local.settings.json for local; Key Vault or App Config recommended later

## Observability plan
- Logs: INFO on start/end, chunk counts, instance IDs
- Metrics: items processed, chunk count, durations, failures (customMetrics)
- KQL starter (App Insights → Logs):
  ```kusto
  traces
  | where timestamp > ago(1h)
  | where message has "Ingestion started orchestration"
  | project timestamp, severityLevel, message
  | order by timestamp desc
  ```

## Performance & cost notes
- Cosmos vector search is low-latency for top-K (tunable by `COSMOS_VECTOR_TOP_K`)
- Fan-out controls parallelism implicitly via Functions host; can throttle activities
- Cost levers: mocked AI mode (`DISABLE_OPENAI=1`), dev-tier Cosmos, batch tests

## Risks & mitigations
- Model quota or throttling → mocked mode and retry/backoff
- Orchestrator anti-patterns → enforce sync orchestrator + async activities review checklist
- Identity misconfig → pre-provision roles; provide RBAC runbook

## Success criteria (technical)
- 100% branch coverage for orchestrator fan-out/fan-in tests
- All orchestrators registered via blueprints; no network I/O in orchestrators
- Async SDK usage across external calls; no awaiting sync APIs
- Deterministic API contracts and error handling

## Event format (1-day sample)
- 09:30 Kickoff: patterns and guardrails
- 10:00 L1 API + persistence
- 11:30 L2 durable fan-out embeddings
- 13:30 L3 vector search + Q&A
- 15:30 L4 blob ingestion + telemetry
- 17:00 Demos, scoring, next steps

## Deliverables
- Working repo (this) with levels 1–4, tests, quickstarts
- Reusable blueprints: orchestrator, activities, blob trigger, query route
- App Insights queries and operational guidance

## Links
- Level guides: `hackathon/level-1.md` … `level-4.md`
- Quickstart: `hackathon/quickstart.md`
- Tests collection: `src/tests/test.http`
