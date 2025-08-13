# Executive Pitch — Snippy AI Hackathon (Extended Edition)

Audience: Directors/Managers/PMO

Summary
- Extended hackathon (6-8 hours) to build an enterprise-grade AI knowledge assistant on Azure Functions (Python), Durable Functions, Cosmos DB (vector search), Azure OpenAI, with advanced multi-agent workflows and zero trust security.
- Outcome: a production-ready backend reference spanning basic AI features through enterprise security patterns, plus comprehensive tests, observability, and compliance monitoring.

Why now
- Accelerates AI feature delivery aligned to modernization OKRs
- Delivers enterprise-grade components for multiple use cases (docs search, support bots, code knowledge, security-compliant AI)
- Time-boxed, progressive complexity, measurable outcomes
- Addresses both AI innovation and security compliance requirements

What participants do
**Core Platform (Levels 1-4):**
- Level 1: API + persistence
- Level 2: Durable fan-out embeddings
- Level 3: Vector search + grounded answers with citations
- Level 4: Blob ingestion + telemetry and resilience

**Advanced Features (Levels 5-6 - Stretch Goals):**
- Level 5: Multi-agent AI orchestration (code review, documentation, testing agents)
- Level 6: Zero trust security (private endpoints, managed identity, compliance)

Business outcomes
- **Technical Capability**: Upskilled teams on Azure serverless + AI + security patterns
- **Accelerated Delivery**: Reference implementation to jump-start projects (6-month faster TTM)
- **Enterprise Readiness**: Production-grade observability, RBAC, and compliance patterns
- **Risk Mitigation**: Security-first AI deployment with zero trust architecture

Success metrics
- % teams completing core levels (L1-L4); advanced levels (L5-L6)
- Demos meeting acceptance criteria across all complexity levels
- Post-event confidence gains in Functions/Durable/Cosmos/AI/Security
- **Reuse impact**: # projects adopting reference patterns in 60 days
- **Security compliance**: Teams demonstrating zero trust implementation

Logistics
- **Audience**: 25–40 engineers (teams of 5–8)
- **Duration**: 6-8 hours (flexible: 6h core + 2h advanced, or 8h comprehensive)
- **Skill paths**: Teams can choose AI focus (L5) or Security focus (L6) for advanced levels
- **Prereqs**: Azure subscription, resource quotas (Cosmos, Storage, App Insights, OpenAI, VNet)

Budget (est.)
- **Cloud services** (dev tiers): <$75/day total (expanded for advanced features)
- **Azure OpenAI tokens**: capped; fallback mocked mode available
- **Network resources**: VNet, private endpoints for L6 (minimal cost)
- **Swag/awards**: TBD

Risks & mitigation
- **Model quota limits** → mocked mode (DISABLE_OPENAI=1), shared endpoints
- **Setup friction** → pre-provision resources, comprehensive setup guides, test automation
- **Time overrun** → progressive levels (L1-L4 core, L5-L6 stretch), strict checkpoints
- **Security complexity** → pre-built Bicep templates, infrastructure automation

Ask
- Approve extended format, quotas, and budget
- Nominate sponsor and facilitators (recommend security SME for L6)
- Greenlight pre-provisioning and infrastructure setup
- **Decision**: 6-hour focused OR 8-hour comprehensive format

Links
- Level guides: hackathon/level-1.md … level-6.md
- Technical pitch: hackathon/pitch-technical.md
- Setup automation: setup-azure-services.md, deploy-azure.sh
