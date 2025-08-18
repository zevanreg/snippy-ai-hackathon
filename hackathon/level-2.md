# Level 2 — Durable Orchestration: Fan-out Embeddings

**🎯 Challenge Points: 20 points (AI Integration Level)**  
*Master asynchronous AI workflows and distributed computing patterns*

## 🎓 Learning Objective
Learn Azure Durable Functions to orchestrate complex AI workflows. Understand fan-out/fan-in patterns, async AI service integration, and how to build resilient, scalable AI processing pipelines.

## 📋 What You're Building
An intelligent orchestration system that takes code snippets, chunks them for optimal processing, generates AI embeddings in parallel, and aggregates results for semantic search. This is the foundation of AI-powered code understanding.

## 🧠 Why Durable Functions Matter for AI
Traditional functions timeout after a few minutes, but AI workflows can take longer and need coordination:
- **Parallel Processing**: Process multiple text chunks simultaneously for speed
- **Reliability**: Handle transient AI service failures with built-in retries
- **State Management**: Track progress of long-running AI operations
- **Cost Optimization**: Only pay for compute when actually processing

## 🛠️ Step-by-Step Implementation Guide

### Step 1: Understanding Durable Function Architecture
Study the existing implementation in `src/functions/bp_embeddings.py`:

1. **Orchestrator Function** (`embeddings_orchestrator`):
   - **Must be sync `def`** (not async) - Durable Functions requirement
   - Uses `yield` to pause execution and wait for activities
   - Coordinates the entire workflow
   - No direct I/O operations (networking, database calls)

2. **Activity Functions** (`embed_chunk_activity`, `persist_snippet_activity`):
   - **Must be async `def`** - Handle I/O operations
   - Return JSON-serializable data only
   - Each handles one specific task

3. **HTTP Starter** (`http_start_embeddings`):
   - Starts the orchestration
   - Returns status URLs for monitoring

### Step 2: Understand the Workflow
The embedding orchestration follows this pattern:

```
📥 HTTP Request → 🎯 Start Orchestrator → 🍰 Chunk Text
                                          ↓
📊 Aggregate Results ← 🔄 Fan-out to Activities → 🤖 Generate Embeddings
                                          ↓
💾 Persist to Cosmos ← 🔄 Fan-in Results ← ⚡ Parallel Processing
```

### Step 3: Code Deep Dive

#### Orchestrator Pattern:
```python
@bp.orchestration_trigger(context_name="context")
def embeddings_orchestrator(context: df.DurableOrchestrationContext) -> Generator[Any, Any, dict]:
    """Fan-out/fan-in to embed chunks and persist a snippet."""
    payload = context.get_input() or {}
    
    # 1. Chunk the text deterministically
    chunks = [text[i : i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
    
    # 2. Fan-out: Create parallel tasks
    tasks = [
        context.call_activity("embed_chunk_activity", {"chunkIndex": i, "text": ch})
        for i, ch in enumerate(chunks)
    ]
    
    # 3. Fan-in: Wait for all results
    embeddings: list[list[float]] = yield context.task_all(tasks)
    
    # 4. Aggregate and persist
    result = yield context.call_activity("persist_snippet_activity", aggregated_data)
```

#### Activity Pattern:
```python
@bp.activity_trigger(input_name="data")
async def embed_chunk_activity(data: str) -> list[float]:
    """Generate an embedding for a text chunk (async)."""
    # Handle both dict and JSON string inputs
    data_dict = json.loads(data) if isinstance(data, str) else data
    
    # Call Azure OpenAI asynchronously
    async with AIProjectClient.from_connection_string(credential=cred, conn_str=conn) as proj:
        async with await proj.inference.get_embeddings_client() as embeds:
            response = await embeds.embed(model=model, input=[text])
```

### Step 4: Key Implementation Details

#### Environment Variables Setup:
The system uses these environment variables (already configured in infrastructure):
- `CHUNK_SIZE` - Size of text chunks (default: 800 characters)
- `EMBEDDING_MODEL_DEPLOYMENT_NAME` - Azure OpenAI embedding model
- `PROJECT_CONNECTION_STRING` - Azure AI Projects connection string
- `DISABLE_OPENAI` - Set to "1" for mock mode during testing

#### Error Handling Patterns:
```python
# Mock mode for testing
if os.environ.get("DISABLE_OPENAI") == "1":
    return [0.0, 1.0, 0.0]  # Deterministic mock embedding

# Graceful degradation
try:
    # Real Azure OpenAI call
    response = await embeds.embed(model=model, input=[text])
    return [float(x) for x in response.data[0].embedding]
except Exception as e:
    logging.error("Embedding failed: %s", e, exc_info=True)
    return []  # Return empty list on failure
```

### Step 5: Testing and Validation

#### Understanding the Test Strategy:
The implementation already includes comprehensive tests. Study the patterns:

1. **Orchestrator Testing**: Mock activity calls and verify fan-out/fan-in logic
2. **Activity Testing**: Mock external services (Azure OpenAI, Cosmos DB)
3. **Integration Testing**: End-to-end workflow validation

#### Mock Patterns for AI Services:
```python
# Mock Azure OpenAI embedding calls
with patch('azure.ai.projects.aio.AIProjectClient.from_connection_string') as mock_client:
    mock_embeddings = AsyncMock()
    mock_embeddings.embed.return_value = Mock(data=[Mock(embedding=[0.1, 0.2, 0.3])])
    # Test your activity function
```

## ✅ Acceptance Criteria
Complete when you can verify:
- ✅ Orchestrator is sync `def` and uses `yield context.task_all()`
- ✅ Activities are async `def` and return JSON-serializable data
- ✅ Text chunking works deterministically
- ✅ Parallel embedding generation completes successfully
- ✅ Results are aggregated and persisted to Cosmos DB
- ✅ HTTP starter returns proper durable function status URLs
- ✅ Error handling works for Azure OpenAI failures
- ✅ Mock mode works for testing without external dependencies
- ✅ All activities log start, progress, and completion

## 🧪 Testing the Implementation

### Cloud Testing with Azure Deployment:

1. **Deploy to Azure:**
   ```bash
   azd auth login
   azd up
   ```

2. **Start an orchestration:**
   ```bash
   # Replace with your actual function app URL from azd output
   export FUNCTION_URL="https://your-function-app.azurewebsites.net"
   
   curl -X POST $FUNCTION_URL/api/orchestrators/embeddings \
     -H "Content-Type: application/json" \
     -d '{
       "projectId": "test-project",
       "name": "example.py", 
       "text": "def hello():\n    print(\"Hello, World!\")\n    return \"success\""
     }'
   ```

Expected response:
```json
{
  "id": "12345",
  "statusQueryGetUri": "https://your-function-app.azurewebsites.net/...",
  "sendEventPostUri": "https://your-function-app.azurewebsites.net/...",
  "terminatePostUri": "https://your-function-app.azurewebsites.net/...",
  "purgeHistoryDeleteUri": "https://your-function-app.azurewebsites.net/..."
}
```

### Monitor Orchestration Progress:
```bash
# Check status (use the statusQueryGetUri from above)
curl "https://your-function-app.azurewebsites.net/runtime/webhooks/durabletask/instances/12345"
```

Successful completion shows:
```json
{
  "runtimeStatus": "Completed",
  "output": {
    "ok": true,
    "id": "example.py"
  }
}
```

## 🚀 Deployment and Testing

### Cloud Deployment with Azure Developer CLI

1. **Deploy the full infrastructure:**
   ```bash
   azd auth login
   azd up
   ```

2. **Test with real embeddings:**
   ```bash
   # Get your function app URL from azd output
   FUNCTION_URL="https://your-function-app.azurewebsites.net"
   
   curl -X POST "$FUNCTION_URL/api/orchestrators/embeddings" \
     -H "Content-Type: application/json" \
     -d '{
       "projectId": "my-project",
       "name": "real-test.py",
       "text": "import numpy as np\n\ndef calculate_distance(p1, p2):\n    return np.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))"
     }'
   ```

Benefits of cloud deployment:
- **Real Azure OpenAI**: Actual embedding generation instead of mocked responses
- **Production Cosmos DB**: Real vector storage and retrieval
- **Full observability**: Complete Application Insights monitoring
- **Scalable processing**: Handles multiple concurrent orchestrations

## 💡 Pro Tips from Your Mentor

### 🔍 Debugging Durable Functions:
- **Check orchestration history**: Use the status URLs to track execution
- **Activity logs**: Each activity logs its progress independently
- **Deterministic execution**: Orchestrators must be deterministic - no random numbers or direct I/O
- **Replay behavior**: Orchestrators replay from checkpoints, so avoid side effects

### 🚀 Performance Optimization:
- **Chunk size tuning**: Experiment with `CHUNK_SIZE` for your content type
- **Parallel processing**: The fan-out pattern automatically scales based on chunk count
- **Connection reuse**: Activities reuse Azure OpenAI connections efficiently
- **Batch processing**: Consider batching multiple small snippets together

### 🛡️ Error Resilience:
- **Transient failures**: Durable Functions automatically retry failed activities
- **Circuit breaker**: The mock mode provides fallback when services are unavailable
- **Timeout handling**: Activities have built-in timeout protection
- **Poison messages**: Failed orchestrations can be inspected and replayed

### 📊 Monitoring and Observability:
- **Application Insights**: All orchestration steps are automatically tracked
- **Custom metrics**: Add custom telemetry for business-specific metrics
- **Correlation IDs**: Each orchestration has a unique instance ID for tracking
- **Performance counters**: Monitor embedding generation latency and throughput

## 🎯 Success Indicators
You've mastered Level 2 when:
1. You understand the fan-out/fan-in pattern for parallel processing
2. You can explain why orchestrators must be sync and activities async
3. Your implementation handles both mock and real AI service modes
4. You can monitor and debug durable function executions
5. The system processes text chunks in parallel efficiently
6. Error handling gracefully manages AI service failures
7. Results are properly aggregated and persisted

**Ready for Level 3?** You'll build vector search and AI-powered Q&A with citations!

---

## 📚 Additional Resources
- [Azure Durable Functions Documentation](https://docs.microsoft.com/en-us/azure/azure-functions/durable/)
- [Azure OpenAI Embeddings API](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/reference)
- [Fan-out/Fan-in Pattern](https://docs.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-cloud-backup)
- [Durable Functions Best Practices](https://docs.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-best-practices)
