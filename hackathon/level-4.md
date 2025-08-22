# Level 4 — Event-driven Ingestion + Observability

**🎯 Challenge Points: 15 points (Operations Level)**  
*Build production-ready automation and monitoring systems*

## 🎓 Learning Objective
Master event-driven architecture, automated content ingestion, and production observability. Learn to build systems that automatically process content and provide comprehensive monitoring for operational excellence.

## 📋 What You're Building
An intelligent automation system that watches for new code files, automatically processes them through your AI pipeline, and provides complete visibility into system health and performance. This transforms your manual workflow into a production-ready service.

## 🧠 Why Event-Driven Architecture Matters
Manual uploads don't scale in production environments:
- **Automatic Processing**: Files are processed immediately upon upload
- **Scalable Ingestion**: Handle hundreds of files without manual intervention  
- **Reliable Delivery**: Event-driven systems provide at-least-once processing guarantees
- **Operational Visibility**: Comprehensive monitoring enables proactive issue resolution
- **Cost Efficiency**: Only process resources when needed

## 🛠️ Step-by-Step Implementation Guide

### Step 1: Understanding Event-Driven Architecture
Study the existing implementation in `src/functions/bp_ingestion.py`:

```
📁 File Upload → 🎯 Blob Trigger → ✅ Validation → 🔄 Start Orchestration → 📊 Monitor Progress
                                      ↓
🚫 Skip Invalid ← 📏 Size Check ← 📄 Content Type ← 🔍 File Analysis
```

The ingestion flow works like this:
1. **Blob Trigger**: Azure Storage automatically invokes function on file upload
2. **Content Validation**: Check file type, size, and format
3. **Text Extraction**: Read and decode file content
4. **Orchestration Start**: Kick off the embeddings pipeline from Level 2
5. **Progress Tracking**: Monitor processing through Application Insights

### Step 2: Blob Trigger Deep Dive

#### Understanding Azure Blob Storage Events:
```python
@bp.blob_trigger(arg_name="blob_client", 
                  path=CONTAINERNAME/OPTIONAL_BLOB_PREFIX,
                  connection="AzureWebJobsStorage")
@bp.durable_client_input(client_name="client")  # Inject orchestration client
async def monitor_ingestion_container(blob_client: blob.BlobClient, df_client: df.DurableOrchestrationClient):
    """Trigger orchestration for uploaded text/markdown file."""
```

This decorator makes sure that for every file that gets added, the function is triggered. 

Go to [bp_ingestion.py](../src/functions/bp_ingestion.py) and implement the function so that `process_blob` is called with the right arguments:

- add the relevant blob_trigger decorator
- call process_blob
- notes: 
    - you can get the blob_name from `blob_client.blob_name`
    - `blob.BlobClient` can be passed as `BlobClient` argument (casting happens automatically)
    - include some logging

Key concepts:
- **Container Watching**: Monitor specific blob containers for new files
- **Event Filtering**: Only process relevant file types and sizes
- **Automatic Scaling**: Azure handles scaling based on upload volume
- **Durable Integration**: Seamlessly start orchestrations from blob events

#### Content Validation and Processing:
```python
# Size validation
size_mb = blob.length / (1024 * 1024)
if size_mb > MAX_BLOB_MB:
    logging.warning("Skipping blob %s: size %.2fMB > limit %dMB", name, size_mb, MAX_BLOB_MB)
    return

# Content type validation  
content_type = getattr(blob, "content_type", "text/plain") or "text/plain"
if not (content_type.startswith("text/") or name.lower().endswith((".md", ".txt", ".py", ".js"))):
    logging.info("Skipping non-text blob: %s (%s)", name, content_type)
    return

# Text extraction with encoding handling
text = blob.read().decode("utf-8", errors="ignore")
```

### Step 3: Orchestration Integration

#### Seamless Pipeline Connection:
```python
# Prepare payload for embeddings orchestration
payload = {
    "projectId": os.environ.get("DEFAULT_PROJECT_ID", "default-project"),
    "name": name,
    "text": text
}

# Start the embeddings orchestration from Level 2
instance_id = await client.start_new("embeddings_orchestrator", None, payload)
logging.info("Ingestion started orchestration id=%s for %s", instance_id, name)
```

This creates a seamless flow:
1. File uploaded to blob storage
2. Blob trigger fires immediately  
3. Content validated and extracted
4. Embeddings orchestration started
5. Text chunked and processed in parallel
6. Results persisted to Cosmos DB
7. All steps monitored and logged

### Step 4: Production Observability

#### Application Insights Integration:
The system provides multiple layers of observability:

1. **Automatic Function Metrics**:
   - Function execution times
   - Success/failure rates
   - Memory and CPU usage
   - Cold start metrics

2. **Custom Telemetry**:
   ```python
   # Custom events for business logic
   logging.info("Ingestion started orchestration id=%s for %s", instance_id, name)
   
   # Performance tracking
   start_time = time.time()
   # ... processing ...
   duration = time.time() - start_time
   logging.info("Processing completed in %.2f seconds", duration)
   
   # Error tracking with context
   try:
       # ... processing ...
   except Exception as e:
       logging.error("Ingestion failed for %s: %s", name, e, exc_info=True)
   ```

3. **Orchestration Monitoring**:
   - Durable function status tracking
   - Activity success/failure rates
   - Processing queue depths
   - End-to-end latency

#### Kusto Query Language (KQL) for Monitoring:
```kusto
// Recent ingestion activity
traces
| where timestamp > ago(1h)
| where message has "Ingestion started orchestration"
| project timestamp, severityLevel, message
| order by timestamp desc

// Error analysis
exceptions
| where timestamp > ago(24h)
| where cloud_RoleName == "your-function-app"
| summarize count() by type, outerMessage
| order by count_ desc

// Performance metrics
customMetrics
| where timestamp > ago(1h)
| where name == "ProcessingDuration"
| summarize avg(value), max(value), min(value) by bin(timestamp, 5m)
| render timechart
```

### Step 5: Error Handling and Resilience

#### Comprehensive Error Handling:
```python
async def ingest_blob(blob: func.InputStream, name: str, client: df.DurableOrchestrationClient):
    """Robust blob ingestion with comprehensive error handling."""
    try:
        # Validation layer
        if not validate_blob(blob, name):
            return
        
        # Content extraction with encoding fallback
        try:
            text = blob.read().decode("utf-8")
        except UnicodeDecodeError:
            text = blob.read().decode("utf-8", errors="ignore")
            logging.warning("Unicode decode errors in %s, using error-ignore mode", name)
        
        # Orchestration startup with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                instance_id = await client.start_new("embeddings_orchestrator", None, payload)
                logging.info("Ingestion started orchestration id=%s for %s", instance_id, name)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logging.warning("Orchestration start failed (attempt %d/%d): %s", 
                              attempt + 1, max_retries, e)
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
    except Exception as e:
        logging.error("Ingestion failed for %s: %s", name, e, exc_info=True)
        # In production, consider dead letter queue or retry policies
```

#### Circuit Breaker Pattern:
```python
# Environment-based circuit breaker
CIRCUIT_BREAKER_ENABLED = os.environ.get("ENABLE_CIRCUIT_BREAKER", "0") == "1"
FAILURE_THRESHOLD = int(os.environ.get("FAILURE_THRESHOLD", "5"))

# Track failures in memory (for demo - use Redis/Cosmos in production)
failure_count = 0

if CIRCUIT_BREAKER_ENABLED and failure_count >= FAILURE_THRESHOLD:
    logging.warning("Circuit breaker open, skipping processing for %s", name)
    return
```

## ✅ Acceptance Criteria
Complete when you can verify:
- ✅ Blob trigger activates on file upload to designated container
- ✅ Content validation filters by file type and size limits
- ✅ Text extraction handles various encodings gracefully
- ✅ Orchestration starts automatically for valid files
- ✅ Application Insights captures all processing events
- ✅ Error handling manages failures without breaking the pipeline
- ✅ Custom metrics track business-relevant performance indicators
- ✅ KQL queries provide operational insights
- ✅ Unit tests for this level succeed

## 🧪 Testing the Implementation

### Cloud Testing with Azure Storage:

1. **Deploy to Azure:**
   ```bash
   azd auth login
   azd up
   ```

2. **Create test files:**
   ```bash
   # Create a Python snippet
   echo 'def hello_world():
       """A simple greeting function."""
       print("Hello, World!")
       return "success"' > test_snippet.py
   
   # Create a markdown document
   echo '# API Documentation
   
   ## Authentication
   Use Bearer tokens for API authentication.
   
   ```python
   headers = {"Authorization": "Bearer <token>"}
   response = requests.get("/api/data", headers=headers)
   ```' > test_docs.md
   ```

3. **Upload and monitor:**
   ```bash
   # Get storage connection string from your deployment
   STORAGE_CONN=$(az storage account show-connection-string \
     --name your-storage-account \
     --resource-group your-resource-group \
     --query connectionString -o tsv)
   
   # Upload using Azure Storage
   az storage blob upload \
     --file test_snippet.py \
     --container-name snippet-input \
     --name test_snippet.py \
     --connection-string "$STORAGE_CONN"
   
   # Monitor function logs in Azure Portal
   az functionapp logs tail --name your-function-app --resource-group your-resource-group
   ```

4. **Expected log output:**
   ```
   [2024-08-18T10:30:15.123Z] Executing 'ingest_blob' (Reason='New blob detected: test_snippet.py')
   [2024-08-18T10:30:15.234Z] Ingestion started orchestration id=abc123 for test_snippet.py
   [2024-08-18T10:30:15.345Z] Executed 'ingest_blob' (Succeeded, Id=def456)
   ```

### Testing Edge Cases:

```bash
# Test file size limit
dd if=/dev/zero of=large_file.txt bs=1M count=5
az storage blob upload --file large_file.txt --container-name snippet-input --name large_file.txt

# Test unsupported file type
echo "binary data" > test.bin
az storage blob upload --file test.bin --container-name snippet-input --name test.bin

# Test Unicode handling
echo "Hello 世界 🌍" > unicode_test.py
az storage blob upload --file unicode_test.py --container-name snippet-input --name unicode_test.py
```

## 🚀 Deployment Options

### Cloud Deployment with Full Infrastructure

1. **Deploy complete infrastructure:**
   ```bash
   azd up
   ```

2. **Configure production settings:**
   ```bash
   # Set environment variables via Azure Portal or CLI
   az functionapp config appsettings set \
     --name your-function-app \
     --resource-group your-resource-group \
     --settings \
     INGESTION_CONTAINER=snippet-input \
     MAX_BLOB_MB=10 \
     ENABLE_CIRCUIT_BREAKER=1
   ```

3. **Test production ingestion:**
   ```bash
   # Get storage connection string
   STORAGE_CONN=$(az storage account show-connection-string \
     --name your-storage-account \
     --resource-group your-resource-group \
     --query connectionString -o tsv)
   
   # Upload test file
   az storage blob upload \
     --file production_snippet.py \
     --container-name snippet-input \
     --name production_snippet.py \
     --connection-string "$STORAGE_CONN"
   ```

4. **Monitor in Application Insights:**
   ```bash
   # Query recent ingestion events
   az monitor app-insights query \
     --app your-app-insights \
     --analytics-query "traces | where timestamp > ago(1h) | where message has 'Ingestion started'"
   ```

## 💡 Pro Tips from Your Mentor

### 🔍 Monitoring Best Practices:
- **Correlation IDs**: Track requests across function boundaries
- **Custom dimensions**: Add business context to telemetry
- **Performance counters**: Monitor processing rates and latencies
- **Alert rules**: Set up proactive notifications for failures

### 🚀 Performance Optimization:
- **Batch processing**: Group small files together for efficiency
- **Content filtering**: Early rejection of inappropriate files
- **Connection pooling**: Reuse storage and database connections
- **Async patterns**: Use async/await throughout the pipeline

### 🛡️ Security and Compliance:
- **Content scanning**: Validate uploaded content for security issues
- **Access logging**: Track who uploads what files
- **Retention policies**: Automatically clean up old files
- **Encryption**: Ensure data is encrypted in transit and at rest

### 📊 Operational Excellence:
- **Health checks**: Implement endpoint monitoring
- **Capacity planning**: Monitor storage and processing limits
- **Disaster recovery**: Plan for region failover scenarios
- **Cost optimization**: Monitor and optimize resource usage

## 🎯 Success Indicators
You've mastered Level 4 when:
1. Files are automatically processed upon upload without manual intervention
2. Comprehensive monitoring provides full visibility into system behavior
3. Error handling gracefully manages various failure scenarios
4. Performance metrics guide optimization decisions
5. RBAC properly secures access to storage and processing resources
6. You can troubleshoot issues using Application Insights queries
7. The system handles production-scale file volumes efficiently

**Ready for Level 5?** You'll implement multi-agent communication and advanced AI workflows!

---

## 📚 Additional Resources
- [Azure Blob Storage Triggers](https://docs.microsoft.com/en-us/azure/azure-functions/functions-bindings-storage-blob-trigger)
- [Application Insights for Azure Functions](https://docs.microsoft.com/en-us/azure/azure-functions/functions-monitoring)
- [KQL (Kusto Query Language)](https://docs.microsoft.com/en-us/azure/data-explorer/kusto/query/)
- [Event-Driven Architecture Patterns](https://docs.microsoft.com/en-us/azure/architecture/guide/architecture-styles/event-driven)
