#!/usr/bin/env python3
"""
Level 1 Cloud Testing Script
Tests the deployed Azure Functions endpoints to validate Level 1 success criteria.
"""

import requests
import json
import sys
import time
import os

# Azure Function App URL from deployment
# Replace these with your actual deployment values
FUNCTION_APP_URL = "https://your-function-app.azurewebsites.net"
FUNCTION_KEY = "your-function-key-here"

def test_health_check():
    """Test the health check endpoint"""
    print("🔄 Testing health check endpoint...")
    
    try:
        response = requests.get(f"{FUNCTION_APP_URL}/api/health", timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data}")
            if data.get("status") == "ok":
                print("   ✅ Health check passed!")
                return True
            else:
                print("   ❌ Health check failed - wrong status")
                return False
        else:
            print(f"   ❌ Health check failed - wrong status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check failed with error: {e}")
        return False

def test_save_snippet():
    """Test saving a code snippet"""
    print("🔄 Testing save snippet endpoint...")
    
    snippet_data = {
        "name": "test-hello-world",
        "code": "print('Hello, World!')",
        "projectId": "level1-test"
    }
    
    headers = {
        "x-functions-key": FUNCTION_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{FUNCTION_APP_URL}/api/snippets", 
            json=snippet_data,
            headers=headers,
            timeout=60
        )
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data}")
            print("   ✅ Save snippet passed!")
            return True
        else:
            print(f"   ❌ Save snippet failed - status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Save snippet failed with error: {e}")
        return False

def test_get_snippet():
    """Test retrieving a code snippet"""
    print("🔄 Testing get snippet endpoint...")
    
    headers = {
        "x-functions-key": FUNCTION_KEY
    }
    
    try:
        response = requests.get(f"{FUNCTION_APP_URL}/api/snippets/test-hello-world", headers=headers, timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data}")
            if data.get("name") == "test-hello-world" and "print('Hello, World!')" in data.get("code", ""):
                print("   ✅ Get snippet passed!")
                return True
            else:
                print("   ❌ Get snippet failed - wrong data returned")
                return False
        elif response.status_code == 404:
            print("   ⚠️  Snippet not found - may need to save first or wait for propagation")
            return False
        else:
            print(f"   ❌ Get snippet failed - status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Get snippet failed with error: {e}")
        return False

def test_list_snippets():
    """Test listing all snippets"""
    print("🔄 Testing list snippets endpoint...")
    
    headers = {
        "x-functions-key": FUNCTION_KEY
    }
    
    try:
        response = requests.get(f"{FUNCTION_APP_URL}/api/snippets", headers=headers, timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data)} snippets")
            if len(data) > 0:
                print(f"   First snippet: {data[0].get('name', 'unknown')}")
            print("   ✅ List snippets passed!")
            return True
        else:
            print(f"   ❌ List snippets failed - status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ List snippets failed with error: {e}")
        return False

def main():
    """Run all Level 1 tests"""
    print("🚀 Starting Level 1 Cloud Testing")
    print("=" * 50)
    
    results = []
    
    # Test 1: Health Check
    results.append(test_health_check())
    print()
    
    # Test 2: Save Snippet
    results.append(test_save_snippet())
    print()
    
    # Wait a moment for data propagation
    print("⏳ Waiting 5 seconds for data propagation...")
    time.sleep(5)
    print()
    
    # Test 3: Get Snippet
    results.append(test_get_snippet())
    print()
    
    # Test 4: List Snippets
    results.append(test_list_snippets())
    print()
    
    # Summary
    print("=" * 50)
    print("📊 LEVEL 1 TEST RESULTS:")
    print(f"   Health Check: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"   Save Snippet: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"   Get Snippet:  {'✅ PASS' if results[2] else '❌ FAIL'}")
    print(f"   List Snippets: {'✅ PASS' if results[3] else '❌ FAIL'}")
    
    total_passed = sum(results)
    print(f"\n🎯 Overall: {total_passed}/4 tests passed")
    
    if total_passed == 4:
        print("🎉 LEVEL 1 COMPLETED SUCCESSFULLY!")
        print("\n✅ All Level 1 Success Criteria Met:")
        print("   - HTTP endpoints deployed and accessible")
        print("   - Health check endpoint working")
        print("   - Save snippet functionality working")
        print("   - Get snippet functionality working")
        print("   - List snippets functionality working")
        print("   - Data persistence in Azure Cosmos DB")
        print("\n🚀 Ready to proceed to Level 2!")
        return 0
    else:
        print("❌ Level 1 not fully complete. Please check the failed tests.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
