# 🚀 Snippy AI Hackathon - Getting Started Guide

Welcome to the Snippy AI Hackathon! This guide will walk you through everything you need to build an enterprise-grade AI-powered knowledge assistant.

## 📋 Prerequisites

- **Azure Subscription** with Contributor/Owner permissions
- **Azure Developer CLI (azd)** - [Install here](https://aka.ms/install-azd)
- **VS Code** with the Azure Functions extension (recommended)
- **Basic knowledge** of Python, Azure Functions, and REST APIs

## 🎯 Challenge Overview

Build a progressive AI knowledge assistant through 6 levels:

### Core Foundation (Required - 6 hours)
- **Level 1** → Foundation API + Persistence
- **Level 2** → Durable Orchestration: Fan-out Embeddings  
- **Level 3** → Vector Search + Q&A with Citations
- **Level 4** → Event-driven Ingestion + Observability

### Advanced Enterprise (Stretch Goals - 2 hours)
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

### Step 3: Verify Deployment
```bash
# Test your deployed endpoint
curl https://your-function-app.azurewebsites.net/api/health

# Expected response:
# {"status": "ok", "timestamp": "2025-08-18T..."}
```

## 🧪 Testing Your Setup

### Basic Functionality Test
```bash
# Upload a test document to trigger ingestion
echo "# Test Document
This is a sample document for testing the AI knowledge assistant." > test-doc.md

# Upload to Azure Storage (triggers automatic processing)
az storage blob upload \
  --file test-doc.md \
  --container-name snippet-input \
  --name test-doc.md \
  --account-name your-storage-account
```

### Query the Knowledge Base
```bash
# Test the Q&A functionality
curl -X POST https://your-function-app.azurewebsites.net/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is this document about?",
    "max_results": 3
  }'
```

## 📚 Level-by-Level Progression

### 🔧 Level 1: Foundation API + Persistence
**Goal**: Create basic CRUD operations for managing code snippets and documents.

**Key Deliverables**:
- Document upload/download endpoints
- Metadata storage in Cosmos DB
- Basic search functionality

**Acceptance Criteria**: 
- ✅ Can store and retrieve documents
- ✅ Basic metadata search works
- ✅ All tests pass

### ⚡ Level 2: Durable Orchestration
**Goal**: Implement fan-out pattern for processing documents with AI embeddings.

**Key Deliverables**:
- Durable Functions orchestrator
- Parallel chunk processing
- Embedding generation with Azure OpenAI

**Acceptance Criteria**:
- ✅ Documents automatically chunked
- ✅ Embeddings generated for all chunks
- ✅ Orchestration handles failures gracefully

### 🔍 Level 3: Vector Search + Q&A
**Goal**: Enable semantic search and AI-powered question answering.

**Key Deliverables**:
- Vector similarity search
- RAG (Retrieval-Augmented Generation)
- Citation tracking

**Acceptance Criteria**:
- ✅ Semantic search returns relevant documents
- ✅ AI generates accurate answers with citations
- ✅ Handles complex queries effectively

### 📊 Level 4: Event-driven Ingestion + Observability
**Goal**: Automated document processing with comprehensive monitoring.

**Key Deliverables**:
- Blob storage trigger
- Application Insights integration
- Error handling and retry logic

**Acceptance Criteria**:
- ✅ Documents auto-processed on upload
- ✅ Comprehensive telemetry and logging
- ✅ Resilient to failures and retries

### 🤖 Level 5: Multi-Agent Orchestration
**Goal**: Specialized AI agents collaborate on complex tasks.

**Key Deliverables**:
- Code reviewer agent
- Documentation agent  
- Testing agent
- Agent communication framework

**Acceptance Criteria**:
- ✅ Agents work together on code analysis
- ✅ Generates comprehensive code reviews
- ✅ Produces documentation and tests

### 🔒 Level 6: Zero Trust Security
**Goal**: Enterprise-grade security with private networking.

**Key Deliverables**:
- Private endpoints for all services
- Managed identity authentication
- Network isolation and monitoring

**Acceptance Criteria**:
- ✅ No public internet access from functions
- ✅ All communication via private networks
- ✅ Complete security audit trail

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
1. **Hours 1-6**: Focus intensely on Levels 1-4
2. **Hours 7-8**: Attempt Levels 5-6 if time permits
3. **Key Success Factor**: Solid implementation of core features

### For Advanced Teams
1. **Parallel Development**: Split team across levels 3-4 and 5-6
2. **Infrastructure First**: Ensure robust foundation
3. **Integration Focus**: Ensure all components work together

### Minimum Viable Product
- Complete Levels 1-4 for a fully functional AI knowledge assistant
- This alone provides significant business value

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
python -m pytest tests/test_level1_endpoints.py -v
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

### Level 5: Multi-Agent (Stretch) ✅
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

1. **Complete the environment setup** (Steps 1-3 above)
2. **Open Level 1 documentation** (`level-1.md`)
3. **Start coding** your AI knowledge assistant!

**Good luck, and happy hacking!** 🎯

---

*Need help? Check the individual level files for detailed implementation guidance, or ask a mentor for architectural advice.*
