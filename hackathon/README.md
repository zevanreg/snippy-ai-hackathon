# Snippy AI Hackathon

A 4-level, hands-on path to build an AI-powered knowledge assistant on Azure Functions (Python v2, blueprint model) with Durable Functions, Cosmos DB vector search, and Azure OpenAI.

## Format
- Duration: 6 hours
- Teams: 5 people per team
- Scoring: Points per level

## Levels
- Level 1 — Foundation API + Persistence
- Level 2 — Durable Orchestration: Fan-out Embeddings
- Level 3 — Vector Search + Q&A with Citations
- Level 4 — Event-driven Ingestion + Observability

See level guides in this folder for detailed tasks, acceptance criteria, and hints.

## Rules
- Python 3.11; Azure Functions Python v2 blueprint model
- Durable orchestrators must be `def` (sync) and use `yield` + `context.task_all(...)`
- Activity functions must be `async def` and return JSON-serialisable data
- Use logging (INFO), type hints, and env vars from `local.settings.json`
- No secrets in code, no prints. Prefer async Azure SDKs.

## Getting started
1. Copy `src/local.settings.example.json` to `src/local.settings.json` and fill secrets.
2. Install deps: `pip install -r src/requirements.txt`.
3. Start Functions locally with the VS Code task "func: host start".
4. Run tests: `python -m pytest -q`.

## Scoring (suggested)
- L1: 20pts — endpoints, tests, logging, env usage
- L2: 30pts — durable pattern, async activities, tests
- L3: 30pts — vector search + Q&A, retries, tests
- L4: 20pts — blob trigger, telemetry, resilience, tests

Happy hacking!
