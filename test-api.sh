#!/bin/bash

# Comprehensive API Testing Script
# Tests all endpoints and workflows

set -e

# Configuration
BASE_URL="${1:-http://localhost:7071}"
OUTPUT_DIR="test-results"

echo "🧪 Starting comprehensive API testing..."
echo "🎯 Target URL: $BASE_URL"

# Create output directory
mkdir -p $OUTPUT_DIR

# Helper function to make requests and save results
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="${5:-200}"
    
    echo "Testing $name..."
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint")
    fi
    
    # Split response and status code
    status_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -n -1)
    
    # Save results
    echo "$body" > "$OUTPUT_DIR/$name.json"
    
    # Check status
    if [ "$status_code" = "$expected_status" ]; then
        echo "✅ $name: Status $status_code (Expected: $expected_status)"
    else
        echo "❌ $name: Status $status_code (Expected: $expected_status)"
    fi
    
    # Pretty print if JSON
    if echo "$body" | jq . >/dev/null 2>&1; then
        echo "$body" | jq . > "$OUTPUT_DIR/$name-formatted.json"
    fi
}

echo "📋 Running Basic CRUD Tests..."

# Test 1: Health Check
test_endpoint "health-check" "GET" "/admin/host/status" ""

# Test 2: List empty snippets
test_endpoint "list-empty" "GET" "/api/snippets" ""

# Test 3: Save snippets
test_endpoint "save-hello" "POST" "/api/snippets" '{
    "name": "hello-world",
    "code": "def hello_world():\n    return \"Hello, World!\"",
    "projectId": "test-project"
}'

test_endpoint "save-fibonacci" "POST" "/api/snippets" '{
    "name": "fibonacci", 
    "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
    "projectId": "algorithms"
}'

test_endpoint "save-quicksort" "POST" "/api/snippets" '{
    "name": "quicksort",
    "code": "def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)",
    "projectId": "algorithms"
}'

# Test 4: List populated snippets
test_endpoint "list-populated" "GET" "/api/snippets" ""

# Test 5: Get specific snippets
test_endpoint "get-hello" "GET" "/api/snippets/hello-world" ""
test_endpoint "get-fibonacci" "GET" "/api/snippets/fibonacci" ""

# Test 6: Error handling
test_endpoint "get-nonexistent" "GET" "/api/snippets/nonexistent" "" "404"

echo "🔍 Running Advanced Feature Tests..."

# Test 7: Query endpoint (may fail in offline mode)
test_endpoint "query-functions" "POST" "/api/query" '{
    "question": "Show me recursive functions",
    "projectId": "algorithms"
}' "200"

# Test 8: RBAC check
test_endpoint "rbac-check" "GET" "/api/security/rbac-check" "" "200"

echo "⚡ Running Orchestrator Tests..."

# Test 9: Multi-agent orchestrator
test_endpoint "multi-agent" "POST" "/api/orchestrators/multi-agent-review" '{
    "name": "test-snippet",
    "code": "def test_function():\n    print(\"This has style issues\")\n    return True"
}' "202"

# Test 10: Embeddings orchestrator  
test_endpoint "embeddings-orch" "POST" "/api/orchestrators/embeddings" '{
    "name": "embedded-snippet",
    "text": "def calculate_average(numbers):\n    return sum(numbers) / len(numbers)",
    "projectId": "math-utils"
}' "202"

echo "🎨 Running AI Agent Tests..."

# Test 11: Deep wiki generation (may fail in offline mode)
test_endpoint "deep-wiki" "POST" "/api/snippets/wiki" '{
    "userQuery": "Generate documentation for my algorithms"
}' "200"

# Test 12: Code style generation (may fail in offline mode)
test_endpoint "code-style" "POST" "/api/snippets/code-style" '{
    "userQuery": "Create a style guide based on my code"
}' "200"

echo "📊 Test Results Summary:"
echo "========================"

# Count results
total_tests=$(ls $OUTPUT_DIR/*.json 2>/dev/null | wc -l)
echo "📈 Total tests executed: $total_tests"

# Show any error responses
echo "❌ Error responses:"
for file in $OUTPUT_DIR/*-formatted.json; do
    if [ -f "$file" ] && grep -q '"error"' "$file"; then
        basename "$file" -formatted.json
        grep '"error"' "$file"
    fi
done

echo "✅ Successful responses:"
for file in $OUTPUT_DIR/*-formatted.json; do
    if [ -f "$file" ] && ! grep -q '"error"' "$file"; then
        echo "  $(basename "$file" -formatted.json)"
    fi
done

echo "📁 Detailed results saved in: $OUTPUT_DIR/"
echo "🔍 View formatted results: ls $OUTPUT_DIR/*-formatted.json"

echo "🎉 Testing completed!"
