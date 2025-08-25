import os
import json
import asyncio
import logging
import sys
import requests
import pytest
import uuid
from unittest.mock import AsyncMock

from functions.bp_snippy import mcp_search_snippets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration - replace with your deployed function app
# FUNCTION_APP_URL = "http://localhost:7071"
FUNCTION_APP_URL = os.getenv("FUNCTION_APP_URL", "https://your-function-app.azurewebsites.net")
FUNCTION_KEY = os.getenv("FUNCTION_KEY", "your-function-key-here")

# Headers for authenticated requests
HEADERS = {
    "Content-Type": "application/json",
    "x-functions-key": FUNCTION_KEY
}

@pytest.mark.asyncio
async def test_1_health_check():
    """Test 1: Verify function app is healthy."""
    logger.info("🔍 Test 1: Health check")
    
    try:
        response = requests.get(f"{FUNCTION_APP_URL}/api/health", headers=HEADERS)
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        
        result = response.json()
        assert result["status"] in ["healthy", "ok"], f"Health status not healthy: {result}"
        
        logger.info("✅ Test 1 PASSED: Function app is healthy")
        
    except Exception as e:
        logger.error(f"❌ Test 1 FAILED: {str(e)}")
        pytest.fail(f"Health check failed: {str(e)}")




@pytest.mark.asyncio
async def test_mcp_search_snippets_missing_query():
    """
    When 'query' is missing, an error JSON should be returned.
    Assumes implementation returns: {"error": "..."}.
    """
    context = json.dumps({"arguments": {"projectid": "proj-alpha"}})
    raw = await mcp_search_snippets(context)
    data = json.loads(raw)
    assert "error" in data, f"Expected error key for missing query: {data}"
    # Optional: loosen assertion if exact message differs
    # assert "query" in data["error"].lower()


@pytest.mark.asyncio
async def test_mcp_search_snippets_invalid_json():
    """
    Invalid JSON input should return a JSON-encoded error.
    """
    raw = await mcp_search_snippets("not-json")
    # Function may already return a JSON string or a plain string;
    # attempt to parse; if parse fails, treat as failure.
    try:
        data = json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        raise AssertionError(f"Expected JSON error response, got raw={raw}") from exc

    assert "error" in data, f"Expected 'error' key for invalid JSON input: {data}"



def main() -> int:
    print("🚀 Starting Level 3.1 Cloud Testing")
    print(f"Target: {FUNCTION_APP_URL}")
    print("=" * 52)

    try:
        # Run each test with individual status messages
        asyncio.run(test_1_health_check())
        print("✅ Health check passed")

        asyncio.run(test_mcp_search_snippets_invalid_json())
        print("✅ MCP invalid JSON handling passed")

        asyncio.run(test_mcp_search_snippets_missing_query())
        print("✅ MCP missing query handling passed")

        print("\n🎉 LEVEL 3.1 COMPLETED SUCCESSFULLY!")
        return 0
    except AssertionError as ae:
        print(f"❌ Test assertion failed: {ae}")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Unexpected error: {type(exc).__name__}: {exc}")
        return 1

if __name__ == "__main__":
    # If invoked by pytest we don't execute main()
    if not any("pytest" in arg for arg in sys.argv):
        sys.exit(main())
