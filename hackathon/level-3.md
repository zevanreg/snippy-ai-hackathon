# Level 3 — Vector Search + Q&A with Citations

**🎯 Challenge Points: 20 points (AI Search Level)**  
*Build intelligent query systems with retrieval-augmented generation (RAG)*

## 🎓 Learning Objective
Master vector search, retrieval-augmented generation (RAG), and AI-powered question answering. Learn to build systems that can find relevant code snippets and generate informed responses with proper citations.

## 📋 What You're Building
An intelligent query system that takes natural language questions, finds relevant code snippets using vector similarity, and generates comprehensive answers with citations. This transforms your snippet collection into a conversational code assistant.

## 🧠 Why Vector Search + RAG Matters
Traditional keyword search fails with code because:
- **Semantic Understanding**: Vector search finds conceptually similar code, not just keyword matches
- **Context Awareness**: RAG combines retrieved context with AI generation for accurate answers
- **Hallucination Prevention**: Grounding AI responses in actual code prevents made-up information
- **Source Attribution**: Citations allow users to verify and explore the original code

## 🛠️ Step-by-Step Implementation Guide

### Step 1: Understanding the Query Architecture
Study the existing implementation in `src/routes/query.py`:

```
🔍 User Question → 🎯 Vector Search → 📚 Retrieve Snippets → 🤖 AI Generation → 📖 Answer + Citations
```

The flow works like this:
1. **RBAC Check**: Verify user permissions for the project
2. **Vector Search**: Find similar code snippets using embeddings
3. **Context Assembly**: Prepare retrieved snippets for AI consumption
4. **AI Generation**: Generate grounded response using chat completion
5. **Citation Extraction**: Return sources for verification

### Step 2: Implement storing of snippets

The solution uses [cosmos_ops](../src/data/cosmos_ops.py) as a central modul to interact with the database. Implement the function to store a snippet in the database. 

1. go to line 133 and implement `upsert_document`.
1. parameters:
   - mandatory: name, project_id, code, embedding
   - optional: language, description
1. use upsert to make sure we can create and insert with a single operation
1. use the integration tests in `test_cloud_level3.py` to verify

### Step 3: Vector Search Deep Dive

#### Understanding Embeddings Similarity:
Vector search works by comparing high-dimensional vectors that represent semantic meaning:
```python
# Question embedding: [0.1, 0.8, 0.3, ...] (1536 dimensions)
# Code snippet 1:    [0.2, 0.7, 0.4, ...] (1536 dimensions) 
# Code snippet 2:    [0.9, 0.1, 0.2, ...] (1536 dimensions)

# Cosine similarity determines relevance:
# Question ↔ Snippet 1: 0.85 (highly relevant)
# Question ↔ Snippet 2: 0.23 (less relevant)
```

#### Vector Search Implementation:
```python
async def vector_search(question: str, project_id: str, top_k: int = 5) -> list[dict]:
    """Find similar snippets using vector search."""
    # 1. Generate embedding for the question
    question_embedding = await generate_embedding(question)
    
    # 2. Query Cosmos DB with vector similarity
    query = """
    SELECT TOP @top_k c.id, c.name, c.code, c.project_id,
           VectorDistance(c.embedding, @question_embedding) AS score
    FROM c 
    WHERE c.project_id = @project_id
    ORDER BY VectorDistance(c.embedding, @question_embedding)
    """
    
    # 3. Execute query and return results
    results = await cosmos_client.query_documents(query, parameters=[...])
    return results
```

### Step 4: RAG Implementation Patterns

#### Context Assembly:
```python
def prepare_context(snippets: list[dict], max_context_length: int = 3000) -> str:
    """Assemble retrieved snippets into context for AI generation."""
    context_parts = []
    current_length = 0
    
    for snippet in snippets:
        snippet_text = f"File: {snippet['name']}\n```\n{snippet['code']}\n```\n"
        if current_length + len(snippet_text) <= max_context_length:
            context_parts.append(snippet_text)
            current_length += len(snippet_text)
        else:
            break  # Respect context window limits
    
    return "\n".join(context_parts)
```

#### AI Generation with Grounding:
```python
async def generate_grounded_response(question: str, context: str) -> str:
    """Generate AI response grounded in retrieved context."""
    system_prompt = """You are a helpful coding assistant. Answer the user's question 
    based ONLY on the provided code snippets. If the information isn't in the snippets, 
    say so. Always cite which files you're referencing."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
    ]
    
    response = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.1  # Low temperature for factual responses
    )
    
    return response.choices[0].message.content
```

### Step 5: Understanding the Complete Implementation

The query endpoint in `src/routes/query.py` implements this full pipeline:

#### RBAC Integration:
```python
@bp.route(route="security/rbac-check", methods=["GET"])
async def rbac_check(req: func.HttpRequest) -> func.HttpResponse:
    """Verify user has access to project resources."""
    # Implementation handles authentication and authorization
    # Returns user permissions and access levels
```

#### Main Query Endpoint:
```python
@bp.route(route="query", methods=["POST"])
async def query_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Main query endpoint with vector search and RAG."""
    try:
        # 1. Parse request
        data = req.get_json()
        question = data.get("question", "")
        project_id = data.get("projectId", "default-project")
        
        # 2. Vector search for relevant snippets
        relevant_snippets = await vector_search_tool.search(
            question=question,
            project_id=project_id,
            top_k=int(os.environ.get("VECTOR_TOP_K", "5"))
        )
        
        # 3. Generate grounded response
        if relevant_snippets:
            context = prepare_context(relevant_snippets)
            answer = await generate_chat_completion(question, context)
            citations = extract_citations(relevant_snippets)
        else:
            answer = "I couldn't find any relevant code snippets for your question."
            citations = []
        
        # 4. Return structured response
        return func.HttpResponse(
            body=json.dumps({
                "answer": answer,
                "citations": citations,
                "usage": {"retrieved_snippets": len(relevant_snippets)}
            }),
            mimetype="application/json"
        )
    except Exception as e:
        # Error handling...
```

### Step 6: Advanced RAG Techniques

#### Citation Extraction:
```python
def extract_citations(snippets: list[dict]) -> list[dict]:
    """Extract citation information from retrieved snippets."""
    return [
        {
            "id": snippet["id"],
            "title": snippet["name"],
            "score": float(snippet.get("score", 0.0)),
            "preview": snippet["code"][:200] + "..." if len(snippet["code"]) > 200 else snippet["code"]
        }
        for snippet in snippets
    ]
```

#### Response Quality Improvements:
- **Temperature Control**: Low temperature (0.1) for factual responses
- **Context Window Management**: Respect AI model token limits
- **Relevance Filtering**: Only include high-scoring results
- **Source Attribution**: Always reference which files are being discussed

## ✅ Acceptance Criteria
Complete when you can verify:
- ✅ Vector search returns relevant code snippets based on semantic similarity
- ✅ RAG system generates responses grounded in retrieved context
- ✅ Citations include file names, relevance scores, and code previews
- ✅ RBAC check validates user access to project resources
- ✅ Error handling manages missing context gracefully
- ✅ Response format is consistent and includes usage metadata
- ✅ Temperature and context window limits are properly configured
- ✅ System refuses to answer questions not covered by retrieved snippets
- ✅ Unit tests for this level succeed

## 🧪 Testing the Implementation

### Cloud Testing with Azure Deployment:

1. **Deploy to Azure:**
   ```bash
   azd auth login
   azd up
   ```

2. **Save some test snippets:**
   ```bash
   # Get your function app URL from azd output
   export FUNCTION_URL="https://your-function-app.azurewebsites.net"
   
   # Save a Python function
   curl -X POST $FUNCTION_URL/api/snippets/database_helper \
     -H "Content-Type: application/json" \
     -d '{
       "code": "async def save_user_data(user_id: str, data: dict):\n    \"\"\"Save user data to database.\"\"\"\n    async with get_db_connection() as conn:\n        await conn.execute(\n            \"INSERT INTO users (id, data) VALUES (?, ?)\",\n            (user_id, json.dumps(data))\n        )\n        await conn.commit()\n    return True"
     }'
   
   # Save a utility function  
   curl -X POST $FUNCTION_URL/api/snippets/json_validator \
     -H "Content-Type: application/json" \
     -d '{
       "code": "def validate_json_schema(data: dict, schema: dict) -> bool:\n    \"\"\"Validate JSON data against schema.\"\"\"\n    try:\n        jsonschema.validate(data, schema)\n        return True\n    except ValidationError:\n        return False"
     }'
   ```

3. **Generate embeddings for the snippets:**
   ```bash
   # Start embedding orchestration for each snippet
   curl -X POST $FUNCTION_URL/api/orchestrators/embeddings \
     -H "Content-Type: application/json" \
     -d '{
       "projectId": "test-project",
       "name": "database_helper",
       "text": "async def save_user_data..."
     }'
   ```

4. **Test the query system:**
   ```bash
   curl -X POST $FUNCTION_URL/api/query \
     -H "Content-Type: application/json" \
     -d '{
       "projectId": "test-project",
       "question": "How do I save user information to a database?"
     }'
   ```

Expected response:
```json
{
  "answer": "Based on the code snippets, you can save user information to a database using the `save_user_data` function from database_helper. This async function takes a user_id (string) and data (dict), connects to the database, executes an INSERT statement, and commits the transaction...",
  "citations": [
    {
      "id": "database_helper",
      "title": "database_helper",
      "score": 0.87,
      "preview": "async def save_user_data(user_id: str, data: dict):\n    \"\"\"Save user data to database.\"\"\"\n    async with get_db_connection() as conn:..."
    }
  ],
  "usage": {
    "retrieved_snippets": 1
  }
}
```

### Testing Query Variations:
```bash
# Test concept-based query
curl -X POST $FUNCTION_URL/api/query \
  -H "Content-Type: application/json" \
  -d '{"projectId": "test-project", "question": "How do I validate JSON data?"}'

# Test implementation-specific query  
curl -X POST $FUNCTION_URL/api/query \
  -H "Content-Type: application/json" \
  -d '{"projectId": "test-project", "question": "Show me async database operations"}'

# Test edge case - no relevant snippets
curl -X POST $FUNCTION_URL/api/query \
  -H "Content-Type: application/json" \
  -d '{"projectId": "test-project", "question": "How do I build a rocket ship?"}'
```

## 🚀 Azure Cloud Deployment

### Full Production Deployment:

1. **Deploy with full infrastructure:**
   ```bash
   azd up
   ```

2. **Test in production environment:**
   ```bash
   FUNCTION_URL="https://your-function-app.azurewebsites.net"
   
   # Test with real Azure OpenAI
   curl -X POST "$FUNCTION_URL/api/query" \
     -H "Content-Type: application/json" \
     -d '{
       "projectId": "production-project",
       "question": "How do I implement error handling in my API endpoints?"
     }'
   ```

3. **Test RBAC endpoint:**
   ```bash
   curl "$FUNCTION_URL/api/security/rbac-check?projectId=test-project&userId=user123"
   ```

Benefits of cloud deployment:
- **Real Vector Search**: Production Cosmos DB vector search capabilities
- **Full AI Integration**: Complete Azure OpenAI chat completion
- **RBAC Enforcement**: Real authentication and authorization
- **Performance Monitoring**: Application Insights tracking

## 💡 Pro Tips from Your Mentor

### 🔍 Query Optimization:
- **Semantic vs Keyword**: Vector search finds conceptually similar code, not just keyword matches
- **Context Window**: Monitor token usage to stay within AI model limits
- **Relevance Thresholds**: Filter out low-scoring results to improve answer quality
- **Question Enhancement**: Consider expanding user questions for better vector search

### 🧠 RAG Best Practices:
- **System Prompts**: Clearly instruct the AI to stay grounded in provided context
- **Temperature Settings**: Use low temperature (0.1-0.2) for factual, grounded responses
- **Citation Format**: Always return which sources informed the response
- **Fallback Handling**: Gracefully handle cases where no relevant context is found

### 📊 Performance Considerations:
- **Embedding Caching**: Reuse question embeddings for similar queries
- **Result Caching**: Cache popular query results for faster responses
- **Parallel Processing**: Generate embeddings and search in parallel when possible
- **Context Prioritization**: Order retrieved snippets by relevance score

### 🛡️ Security and Quality:
- **RBAC Integration**: Always verify user permissions before returning results
- **Input Sanitization**: Validate and sanitize all user queries
- **Content Filtering**: Prevent inappropriate or sensitive information leakage
- **Audit Logging**: Track all queries for security and analytics

## 🎯 Success Indicators
You've mastered Level 3 when:
1. Your vector search finds semantically relevant code snippets
2. RAG generates accurate, grounded responses with proper citations
3. You understand the difference between semantic and keyword search
4. RBAC properly controls access to project resources
5. Error handling gracefully manages edge cases
6. Performance is optimized for production workloads
7. You can explain how embeddings enable semantic search

**Ready for Level 4?** You'll integrate with GitHub Copilot via MCP tools!

---

## 📚 Additional Resources
- [Vector Search in Azure Cosmos DB](https://docs.microsoft.com/en-us/azure/cosmos-db/vector-search)
- [Retrieval Augmented Generation (RAG)](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/concepts/use-your-data)
- [Azure OpenAI Chat Completions](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/reference)
- [Semantic Search Best Practices](https://docs.microsoft.com/en-us/azure/search/search-get-started-semantic)
