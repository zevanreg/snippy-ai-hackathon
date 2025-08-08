# Executive Pitch — Snippy AI Hackathon

Audience: Directors/Managers/PMO

Summary
- 1‑day hands-on hackathon to build an AI knowledge assistant on Azure Functions (Python), Durable Functions, Cosmos DB (vector search), and Azure OpenAI.
- Outcome: a production‑aligned backend reference (ingestion → embeddings → vector search → grounded Q&A) plus tests, observability, and RBAC patterns.

Why now
- Accelerates AI feature delivery aligned to modernization OKRs.
- Delivers reusable components for multiple use cases (docs search, support bots, code knowledge).
- Time‑boxed, low‑risk, measurable outcomes.

What participants do
- Level 1: API + persistence
- Level 2: Durable fan‑out embeddings
- Level 3: Vector search + grounded answers with citations
- Level 4: Blob ingestion + telemetry and resilience

Business outcomes
- Upskilled teams on Azure serverless + AI patterns
- Reference implementation to jump‑start projects
- Improved operational readiness (App Insights, KQL, RBAC)

Success metrics
- % teams completing each level; tests passing
- Demos meeting acceptance criteria
- Post‑event confidence gains in Functions/Durable/Cosmos/AI
- Reuse: # projects adopting reference in 60 days

Logistics
- Audience: 25–40 engineers (teams of 5–8)
- Duration: 1 day (or two half‑days)
- Prereqs: Azure subscription, resource quotas (Cosmos, Storage, App Insights, OpenAI)

Budget (est.)
- Cloud services (dev tiers): <$50/day total (ex‑OpenAI)
- Azure OpenAI tokens: capped; fallback mocked mode available
- Swag/awards: TBD

Risks & mitigation
- Model quota limits → mocked mode (DISABLE_OPENAI=1), shared endpoints
- Setup friction → pre‑provision resources, Quickstart docs, test.http
- Time overrun → strict checkpoints, facilitator support

Ask
- Approve date, quotas, and light budget
- Nominate sponsor and facilitators
- Greenlight pre‑provisioning and comms

Links
- Level guides: hackathon/level-1.md … level-4.md
- Technical pitch: hackathon/pitch-technical.md
- Quickstart: hackathon/quickstart.md
