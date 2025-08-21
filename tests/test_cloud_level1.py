#!/usr/bin/env python3
"""
Level 1 Cloud Testing Script
Tests the deployed Azure Functions endpoints to validate Level 1 success criteria.
"""

import requests
import pytest
import sys
import time
import os

# Azure Function App URL from deployment
# Replace these with your actual deployment values
FUNCTION_APP_URL = os.getenv("FUNCTION_APP_URL", "https://your-function-app.azurewebsites.net") 
FUNCTION_KEY = os.getenv("FUNCTION_KEY", "your-function-key-here")

def test_health_check():
    """Test the health check endpoint"""
    response = requests.get(f"{FUNCTION_APP_URL}/api/health", timeout=30)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data.get("status") == "ok", f"Expected status 'ok', got {data.get('status')}"

def test_save_snippet():
    """Test saving a code snippet"""
    snippet_data = {
        "name": "test-hello-world",
        "code": "print('Hello, World!')",
        "projectId": "level1-test"
    }
    
    headers = {
        "x-functions-key": FUNCTION_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{FUNCTION_APP_URL}/api/snippets", 
        json=snippet_data,
        headers=headers,
        timeout=60
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    # Wait for data propagation
    time.sleep(2)

def test_get_snippet():
    """Test retrieving a code snippet"""
    headers = {
        "x-functions-key": FUNCTION_KEY
    }
    
    response = requests.get(f"{FUNCTION_APP_URL}/api/snippets/test-hello-world", headers=headers, timeout=30)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    assert data.get("name") == "test-hello-world", f"Expected name 'test-hello-world', got {data.get('name')}"
    assert "print('Hello, World!')" in data.get("code", ""), "Expected code content not found"

def test_list_snippets():
    """Test listing all snippets"""
    headers = {
        "x-functions-key": FUNCTION_KEY
    }
    
    response = requests.get(f"{FUNCTION_APP_URL}/api/snippets", headers=headers, timeout=30)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    assert isinstance(data, list), "Expected response to be a list"
    # Note: We don't assert len(data) > 0 because the list might be empty in a clean environment

def main():
    """Run all Level 1 tests in standalone mode"""
    print("🚀 Starting Level 1 Cloud Testing")
    print("=" * 50)
    
    try:
        test_health_check()
        print("✅ Health check passed!")
        
        test_save_snippet()
        print("✅ Save snippet passed!")
        
        time.sleep(3)  # Extra wait for propagation
        
        test_get_snippet()
        print("✅ Get snippet passed!")
        
        test_list_snippets()
        print("✅ List snippets passed!")
        
        print("\n🎉 LEVEL 1 COMPLETED SUCCESSFULLY!")
        return 0
        
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
