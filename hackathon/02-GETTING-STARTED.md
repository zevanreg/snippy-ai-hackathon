# 🚀 Snippy AI Hackathon - Getting Started Guide

Welcome to the Snippy AI Hackathon! This guide will walk you through everything you need to build an enterprise-grade AI-powered knowledge assistant.

## 📋 Prerequisites

- **Azure Subscription** with Contributor/Owner permissions
- **Azure Developer CLI (azd)** - [Install here](https://aka.ms/install-azd)
- **VS Code** with the Azure Functions extension (recommended)
- **Basic knowledge** of Python, Azure Functions, and REST APIs

## 🎯 Challenge Overview

Build a progressive AI knowledge assistant through 6 levels:

- **Level 1** → Foundation API + Persistence
- **Level 2** → Durable Orchestration: Fan-out Embeddings  
- **Level 3** → Vector Search + Q&A with Citations
- **Level 4** → Event-driven Ingestion + Observability
- **Level 5** → Multi-Agent Orchestration
- **Level 6** → Zero Trust Network Security

## 🛠️ Environment Setup

### Step 1: Initial Setup
```bash
# Clone the repository (if not already done)
git clone https://github.com/cihanduruer/snippy-ai-hackathon
cd snippy-ai-hackathon

# Authenticate with Azure
az login
azd auth login
```

### Step 2: Deploy Infrastructure
```bash
# Create a new environment
azd env new "your-team-name-hackathon"

# Deploy complete Azure infrastructure (this takes ~20 minutes)
azd up
```

**☕ Coffee break time!** The deployment creates:
- Azure Functions (Python 3.11)
- Cosmos DB with vector search
- Azure Storage Account
- Azure AI Foundry (OpenAI models)
- Application Insights
- All necessary security and networking


## 🛡️ Technical Requirements

### Code Standards
- **Python 3.11** with type hints
- **Azure Functions Python v2** blueprint model
- **Durable orchestrators**: `def` (sync) with `yield` + `context.task_all(...)`
- **Activity functions**: `async def` returning JSON-serializable data
- **Logging**: Use `logging` (INFO level) instead of `print`
- **Security**: No secrets in code, use environment variables

### Architecture Patterns
- **Fan-out/Fan-in**: For parallel processing
- **Event-driven**: Blob triggers for automation
- **RAG Pattern**: For AI-powered Q&A
- **Circuit Breaker**: For resilience
- **Zero Trust**: For enterprise security

## 🎯 Winning Strategy

### For Teams Aiming for Completion (Recommended)
1. **Hours 1-5**: Focus intensely on Levels 1-5
2. **Hours 5-6**: Attempt Level 6 if time permits
3. **Key Success Factor**: Solid implementation of core features

### For Advanced Teams
1. **Parallel Development**: Split team across levels 3-4 and 5-6
2. **Infrastructure First**: Ensure robust foundation
3. **Integration Focus**: Ensure all components work together

## 🔧 Development Workflow

### Making Changes
```bash
# Deploy code changes
azd deploy

# Or deploy everything if infrastructure changed
azd up
```

### Testing Changes
```bash
# Run local tests
cd src
python -m pytest tests/ -v

# Test specific level
python -m pytest tests/test_cloud_level1.py -v
```

### Monitoring and Debugging
```bash
# View application logs
az functionapp logs tail \
  --name your-function-app \
  --resource-group your-resource-group

# Query Application Insights
# Go to Azure Portal → Application Insights → Logs
```

Useful KQL queries:
```kusto
// View recent function executions
requests 
| where timestamp > ago(1h)
| project timestamp, name, success, duration
| order by timestamp desc

// Find errors
exceptions
| where timestamp > ago(1h)
| project timestamp, problemId, outerMessage
```

## 🆘 Troubleshooting

### Common Issues

**Deployment Failures**:
```bash
# Check deployment logs
azd provision --debug

# Verify resource permissions
az account show --query "{subscription:id, tenant:tenantId}"
```

**Function Errors**:
- Check Azure Portal → Function App → Monitor
- Verify environment variables are set correctly
- Ensure Managed Identity has required permissions

**Storage Issues**:
- Verify container names match configuration
- Check storage account connection string
- Ensure blob trigger is properly configured

**AI Service Issues**:
- Verify Azure AI Foundry deployment
- Check model deployment status
- Validate API endpoints and keys

### Getting Help
1. **Check level-specific documentation** in `level-*.md` files
2. **Review Azure Portal** for service status and logs
3. **Use Application Insights** for detailed telemetry
4. **Ask mentors** for architecture and implementation guidance

## 🎉 Completion Checklist

### Level 1: Foundation ✅
- [ ] Document CRUD operations working
- [ ] Cosmos DB integration complete
- [ ] Basic search functionality
- [ ] All Level 1 tests passing

### Level 2: Durable Functions ✅
- [ ] Orchestrator successfully fans out
- [ ] Embeddings generated for documents
- [ ] Parallel processing working
- [ ] All Level 2 tests passing

### Level 3: Vector Search ✅
- [ ] Semantic search returning relevant results
- [ ] Q&A with proper citations
- [ ] Vector database queries optimized
- [ ] All Level 3 tests passing

### Level 4: Event-driven + Observability ✅
- [ ] Blob trigger processing documents automatically
- [ ] Comprehensive Application Insights telemetry
- [ ] Error handling and retry logic
- [ ] All Level 4 tests passing

### Level 5: Multi-Agent ✅
- [ ] Multiple AI agents collaborating
- [ ] Agent communication framework
- [ ] Complex task orchestration
- [ ] All Level 5 tests passing

### Level 6: Zero Trust (Stretch) ✅
- [ ] Private endpoints implemented
- [ ] Network isolation complete
- [ ] Security monitoring active
- [ ] All Level 6 tests passing

## 🚀 Ready to Start?

1. **Complete the environment setup** (Steps 1 and 2 above)
2. **Open Level 1 documentation** (`level-1.md`)
3. **Start coding** your AI knowledge assistant!

**Good luck, and happy hacking!** 🎯

---

*Need help? Check the individual level files for detailed implementation guidance, or ask a mentor for architectural advice.*
