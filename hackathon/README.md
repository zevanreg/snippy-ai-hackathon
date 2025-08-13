# Snippy AI Hackathon

A 6-level, hands-on path to build an enterprise-grade AI-powered knowledge assistant on Azure Functions (Python v2, blueprint model) with Durable Functions, Cosmos DB vector search, Azure OpenAI, and Zero Trust security.

## Format
- Duration: 8 hours (core levels L1-L4: 6 hours, advanced levels L5-L6: 2 hours)
- Teams: 5 people per team

## Levels

### Core Foundation (Required)
- **Level 1** — Foundation API + Persistence
- **Level 2** — Durable Orchestration: Fan-out Embeddings
- **Level 3** — Vector Search + Q&A with Citations
- **Level 4** — Event-driven Ingestion + Observability

### Advanced Enterprise Features (Stretch Goals)
- **Level 5** — Agent-to-Agent Communication: Multi-Agent Orchestration
- **Level 6** — Zero Trust Network: Private Endpoints + Egress Lockdown

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

## Completion Strategy
- **Teams aiming for completion**: Focus on L1-L4 first (6 hours), then attempt L5-L6 (2 hours)
- **Advanced teams**: Can tackle L5-L6 in parallel with L3-L4 if infrastructure allows
- **Minimum viable**: L1-L4 provides a fully functional AI knowledge assistant

## Key Technical Differentiators

### Levels 1-4: Foundation Platform
Build a solid, production-ready AI knowledge assistant with CRUD operations, vector search, and automated ingestion.

### Level 5: AI Agent Orchestration
Transform your assistant into a multi-agent system where specialized AI agents collaborate on complex tasks like code review, documentation, and testing.

### Level 6: Enterprise Security
Implement zero trust security with private networking, managed identity, and compliance monitoring suitable for enterprise deployment.

Happy hacking!
