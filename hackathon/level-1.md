# Level 1 — Foundation API + Persistence

**🎯 Challenge Points: 10 points (Foundation Level)**  
*Your first step into building a production-ready AI code assistant*

## 🎓 Learning Objective
Master the fundamentals of Azure Functions with Python, implement RESTful APIs, and establish secure database persistence patterns. This level builds the foundation for all advanced features.

## 📋 What You're Building
A robust HTTP API that can save, retrieve, and manage code snippets with proper validation, error handling, and logging. Think of this as the backbone of your AI assistant - every snippet operation flows through these endpoints.

## 🛠️ Step-by-Step Implementation Guide

### Step 1: Understanding the Architecture
Before coding, familiarize yourself with the existing structure:
- `src/function_app.py` - Main application entry point with health check
- `src/functions/bp_snippy.py` - Primary Python code file which defines the Snippy MCP tool functionality with snippet operations (already implemented!)
- `src/data/cosmos_ops.py` - Database operations helper
- `src/routes/query.py` - Query functionality (added in later levels)

### Step 2: Health Check Verification
A simple health endpoint is already implemented in `function_app.py`. Verify it returns HTTP 200 and:
```json
{"status": "ok"}
```

**Test it with Azure deployment:**
```bash
# Deploy to Azure first - this can take some 10-20 minutes
az login
azd up

# Test with your deployed function URL
curl https://your-function-app.azurewebsites.net/api/health
```


### Step 3: Implement extended health test

We have a health test showing the endpoint is reachable. Implement an extended health-test that we can call to know if the azure function can successfully connect to the storage account and cosmosDB. 

Start your implementation in [`src/function_app.py`](../src/function_app.py) at line 113. Some hints:

- Right now the REST-endpoint returns [https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/418](418) which seems wrong 🫖😅.
- Look at the endpoint at line 88 to understand how to return a proper result. 
- The connection details are all in environment variables
- use the unit-test [`tests/test_cloud_level1.py`](../tests/test_cloud_level1.py) to check your result
- run `azd deploy` to deploy your code

### Step 4: Verify Existing Endpoints
**Good news!** (most) of the snippet endpoints already exist in `bp_snippy.py`. Your task is to:

1. **Review the existing implementation** in `src/functions/bp_snippy.py`
   - Look at the `save_snippet` function (POST /snippets/{snippet_name})
   - Examine the `get_snippet` function (GET /snippets/{snippet_name})
   - Understand how they use `cosmos_ops.py` for database operations

2. **Ensure proper validation** - Review the code that validate inputs in each function:
   ```python
   # Example validation pattern to look for:
   if not name or not code:
       return func.HttpResponse("Missing name or code", status_code=400)
   ```

3. **Add comprehensive logging** - Replace any `print()` with `logging.info()`:
   ```python
   logging.info(f"Saving snippet: {name} for project: {project_id}")
   ```

4. **Verify error handling** - Ensure proper HTTP status codes:
   - 200-299 for successful operations
   - 400-499 for bad requests
     - 404 for not found
   - 500-599 for server errors

### Step 5: Code Quality Standards
As you review and enhance the code, ensure:

- **Type hints everywhere**: 
  ```python
  def save_snippet(req: func.HttpRequest) -> func.HttpResponse:
  ```

- **Proper logging**: 
  ```python
  logging.info(f"Saving snippet: {name}")
  logging.error(f"Error saving snippet: {str(e)}")
  ```

- **Environment variables**: 
  ```python
  project_id = os.environ.get("DEFAULT_PROJECT_ID", "default-project")
  ```

- **No hardcoded secrets**: All sensitive data from environment

- **Async/await patterns**: Don't await synchronous methods like `req.get_json()`

### Step 6: Database Integration Deep Dive
Review how `data/cosmos_ops.py` is used:

1. **Understand the `upsert_document()` function:**
   ```python
   # Saves or updates a snippet with embedding
   result = await cosmos_ops.upsert_document(
       name=name, 
       project_id=project_id, 
       code=code, 
       embedding=embedding
   )
   ```

2. **See how `query_documents()` retrieves data:**
   ```python
   # Retrieves a specific snippet
   result = await cosmos_ops.query_documents(
       query="SELECT * FROM c WHERE c.name = @name",
       parameters=[{"name": "@name", "value": name}]
   )
   ```

3. **Note the async patterns and error handling:**
   - All database operations are async
   - Proper exception handling with try/catch blocks
   - Meaningful error messages

## ✅ Acceptance Criteria
Complete when you can verify:
- ✅ Health endpoint returns 200 with `{"status":"ok"}`
- ✅ POST /snippets/{name} accepts snippet data and returns success/error
- ✅ GET /snippets/{name} returns snippet data or 404
- ✅ All responses use proper HTTP status codes
- ✅ No synchronous APIs are awaited
- ✅ All secrets come from environment variables
- ✅ Comprehensive logging at INFO level
- ✅ Type hints on all functions
- ✅ All unit tests for level 1 (`test_cloud_level1.py`) are successful

## 🧪 Testing Strategy

Look at `tests/test_level1_endpoints.py` with these test cases:

### Positive Test Cases:
```python
@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check returns 200 OK"""
    
@pytest.mark.asyncio  
async def test_save_snippet_success():
    """Test saving a valid snippet"""
    
@pytest.mark.asyncio
async def test_get_snippet_success():
    """Test retrieving an existing snippet"""
```

### Negative Test Cases:
```python
@pytest.mark.asyncio
async def test_save_snippet_invalid_data():
    """Test saving with missing required fields"""
    
@pytest.mark.asyncio
async def test_get_nonexistent_snippet():
    """Test retrieving a snippet that doesn't exist"""
```

## 💡 Pro Tips from Your Mentor

### 🔍 Debugging Tips:
- **Test locally**: azd will generate a `local.settings.json`file so you can cd into the src folder and run `func host start` to run the functions locally.
- **Check function logs**: Use Azure Portal or Azure CLI to view logs from deployed functions
- **Environment variables**: Ensure all required settings are configured in Azure
- **JSON handling**: Always validate JSON input before processing
- **Error responses**: Return meaningful error messages with appropriate status codes

### 🛡️ Security Best Practices:
- **Environment isolation**: Keep secrets in environment variables
- **Least privilege**: Only grant necessary permissions to your function app
- **Request limits**: Consider implementing rate limiting for production use

### 📈 Performance Considerations:
- **Connection pooling**: Cosmos client should be reused across function calls
- **Async operations**: Use async/await for all I/O operations
- **Error handling**: Implement proper retry logic for transient failures
- **Monitoring**: Add Application Insights for production monitoring

## 🎯 Success Indicators
You've successfully completed Level 1 when:
1. All endpoints respond correctly with proper status codes
2. Data persists to Cosmos DB successfully
3. All tests pass
4. Code follows Azure Functions Python best practices
5. No hardcoded secrets or configuration values
6. Comprehensive logging throughout the application

**Ready for Level 2?** You'll add AI-powered embedding generation with Durable Functions orchestration!

---

## 📚 Additional Resources
- [Azure Functions Python Developer Guide](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [Azure Cosmos DB Python SDK](https://docs.microsoft.com/en-us/azure/cosmos-db/sql/sql-api-sdk-python)
- [Azure Functions Best Practices](https://docs.microsoft.com/en-us/azure/azure-functions/functions-best-practices)
