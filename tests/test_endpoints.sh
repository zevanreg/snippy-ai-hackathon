#!/bin/bash
# =============================================================================
# Snippy Azure Functions Endpoint Testing Script
# =============================================================================

# Configuration
FUNCTION_APP_URL="https://func-s2wsaefugjcvy.azurewebsites.net"
FUNCTION_KEY="Y36BWOh9zsGA19BxFbF6SEZb7-_-4dV_NLRmdh3nr40mAzFu6oq2Tg=="

echo "🧪 Testing Snippy Azure Functions Endpoints"
echo "=========================================="
echo "Function App: $FUNCTION_APP_URL"
echo ""

# Test 1: Health Check
echo "🏥 Test 1: Health Check"
echo "------------------------"
curl -w "Status: %{http_code}\n" -s "$FUNCTION_APP_URL/api/health" | jq . 2>/dev/null || echo "Response received"
echo ""

# Test 2: Save a Snippet
echo "📝 Test 2: Save a Code Snippet"
echo "-------------------------------"
curl -w "Status: %{http_code}\n" -s -X POST "$FUNCTION_APP_URL/api/snippets" \
  -H "x-functions-key: $FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello-world-test",
    "projectId": "test-project",
    "code": "def hello_world():\n    print(\"Hello from Snippy!\")\n    return \"success\""
  }' | jq . 2>/dev/null || echo "Response received"
echo ""

# Test 3: List Snippets
echo "📋 Test 3: List All Snippets"
echo "-----------------------------"
curl -w "Status: %{http_code}\n" -s "$FUNCTION_APP_URL/api/snippets?projectId=test-project" \
  -H "x-functions-key: $FUNCTION_KEY" | jq . 2>/dev/null || echo "Response received"
echo ""

# Test 4: Upload File for Processing
echo "📁 Test 4: Upload File for Processing"
echo "--------------------------------------"
curl -w "Status: %{http_code}\n" -s -X POST "$FUNCTION_APP_URL/api/ingestion/upload" \
  -H "x-functions-key: $FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "api_utils.py",
    "content": "import requests\n\ndef call_api(url, data=None):\n    \"\"\"Make an API call with error handling.\"\"\"\n    try:\n        response = requests.post(url, json=data)\n        response.raise_for_status()\n        return response.json()\n    except requests.RequestException as e:\n        print(f\"API error: {e}\")\n        return None"
  }' | jq . 2>/dev/null || echo "Response received"
echo ""

# Test 5: Vector Search Query
echo "🔍 Test 5: Vector Search Query"
echo "-------------------------------"
curl -w "Status: %{http_code}\n" -s -X POST "$FUNCTION_APP_URL/api/query" \
  -H "x-functions-key: $FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "hello world function",
    "projectId": "test-project",
    "maxResults": 3
  }' | jq . 2>/dev/null || echo "Response received"
echo ""

# Test 6: Multi-Agent Code Review
echo "🤖 Test 6: Multi-Agent Code Review"
echo "-----------------------------------"
ORCHESTRATION_RESPONSE=$(curl -s -X POST "$FUNCTION_APP_URL/api/orchestrators/multi-agent-review" \
  -H "x-functions-key: $FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "snippetId": "hello-world-test",
    "correlationId": "test-review-001"
  }')

echo "Orchestration started:"
echo $ORCHESTRATION_RESPONSE | jq . 2>/dev/null || echo $ORCHESTRATION_RESPONSE
echo ""

# Test 7: AI Style Guide Generation
echo "📖 Test 7: AI Style Guide Generation"
echo "-------------------------------------"
curl -w "Status: %{http_code}\n" -s -X POST "$FUNCTION_APP_URL/api/snippets/code-style" \
  -H "x-functions-key: $FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "test-project"
  }' | jq . 2>/dev/null || echo "Response received"
echo ""

# Test 8: AI Wiki Documentation
echo "📚 Test 8: AI Wiki Documentation Generation"
echo "--------------------------------------------"
curl -w "Status: %{http_code}\n" -s -X POST "$FUNCTION_APP_URL/api/snippets/wiki" \
  -H "x-functions-key: $FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "test-project"
  }' | jq . 2>/dev/null || echo "Response received"
echo ""

echo "✅ All endpoint tests completed!"
echo ""
echo "🎉 MCP (Model Context Protocol) endpoints are now implemented!"
echo "   Available MCP tools:"
echo "   - save_snippet: Save code snippets with automatic embeddings"
echo "   - get_snippet: Retrieve snippets by name"
echo "   - search_snippets: Semantic search across snippets"
echo "   - list_snippets: List all available snippets"
echo "   - delete_snippet: Delete snippets (placeholder - not yet fully implemented)"
echo "   - code_style: Generate AI-powered style guides"
echo "   - deep_wiki: Generate comprehensive documentation"
echo ""
echo "📖 To use MCP tools with GitHub Copilot:"
echo "   1. Configure the MCP client using .vscode/mcp.json"
echo "   2. Use the SSE endpoint: /runtime/webhooks/mcp/sse"
echo "   3. Tools will be available in AI assistants that support MCP"
