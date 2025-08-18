# 🎯 Snippy AI Hackathon

Build an enterprise-grade AI-powered knowledge assistant using Azure Functions, Cosmos DB vector search, Azure OpenAI, and Zero Trust security.

## 🚀 Quick Start

**👉 [Read the complete Getting Started Guide](./GETTING-STARTED.md)**

```bash
# 1. Authenticate
azd auth login

# 2. Deploy everything
azd env new "your-team-name"
azd up

# 3. Start building!
```

## 📊 Challenge Structure

### 🎯 Format
- **Duration**: 6 hours total
- **Teams**: 5 people per team
- **Tech Stack**: Azure Functions (Python 3.11), Cosmos DB, Azure OpenAI, Durable Functions

### 🏆 Levels Overview

#### Core Foundation (Required - 6 hours)
| Level | Focus | Key Deliverable |
|-------|--------|-----------------|
| **Level 1** | Foundation API + Persistence | CRUD operations, metadata storage |
| **Level 2** | Durable Orchestration | Fan-out embeddings, parallel processing |
| **Level 3** | Vector Search + Q&A | Semantic search, RAG with citations |
| **Level 4** | Event-driven + Observability | Auto-ingestion, monitoring, resilience |

#### Advanced Enterprise (Stretch Goals - 2 hours)
| Level | Focus | Key Deliverable |
|-------|--------|-----------------|
| **Level 5** | Multi-Agent Orchestration | AI agents collaborating on complex tasks |
| **Level 6** | Zero Trust Security | Private endpoints, network isolation |

## 🎯 Winning Strategy

### ✅ Teams Aiming for Completion
1. **Focus on Levels 1-4 first** (4 hours)
2. **Attempt Levels 5-6** if time permits (2 hours)
3. **Prioritize solid implementation** over feature breadth

### 🚀 Advanced Teams
1. **Split effort** between core (Levels 1-4) and advanced (Levels 5-6)
2. **Ensure integration** between all components
3. **Focus on architecture** and scalability

### 🎖️ Minimum Viable Product
Complete **Levels 1-4** for a fully functional AI knowledge assistant with:
- Document ingestion and storage
- AI-powered semantic search
- Question answering with citations
- Automated processing and monitoring

## 📋 Technical Requirements

- **Python 3.11** with Azure Functions v2 blueprint model
- **Durable orchestrators**: `def` (sync) with `yield` + `context.task_all(...)`
- **Activity functions**: `async def` returning JSON-serializable data
- **Cloud-first deployment**: Use `azd up` for all development and testing
- **No local development**: All testing against deployed Azure resources
- **Security**: No secrets in code, use environment variables and Managed Identity

## 🎉 Ready to Build?

1. **[Follow the Getting Started Guide](./GETTING-STARTED.md)** for complete setup instructions
2. **Open Level 1** (`level-1.md`) for your first challenge
3. **Start coding** your AI knowledge assistant!

**Good luck, and happy hacking!** 🚀
