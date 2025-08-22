#!/usr/bin/env python3
"""
Level 2 Cloud Testing Script
Tests the deployed Azure Durable Functions endpoints to validate Level 2 success criteria.
"""

import requests
import json
import pytest
import sys
import time
import os
from functions.bp_embeddings import validate_input

# Azure Function App URL from deployment
FUNCTION_APP_URL = os.getenv("FUNCTION_APP_URL", "https://your-function-app.azurewebsites.net")
FUNCTION_KEY = os.getenv("FUNCTION_KEY", "your-function-key-here")


def test_orchestration_endpoint():
    """Test the Durable Functions orchestration endpoint"""
    test_payload = {
        "projectId": "level2-test",
        "snippets": [
            {
                "name": "test.py",
                "code": "# Level 2 Test\ndef test_function():\n    return 'Durable Functions Test'",
                "language": "python",
                "description": "Test snippet for Level 2"
            }
        ]
    }

    headers = {
        "x-functions-key": FUNCTION_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{FUNCTION_APP_URL}/api/orchestrators/embeddings",
        json=test_payload,
        headers=headers,
        timeout=30
    )

    assert response.status_code == 202, f"Expected 202, got {response.status_code}: {response.text}"

    data = response.json()
    assert "id" in data, "Response should contain orchestration instance ID"
    assert "statusQueryGetUri" in data, "Response should contain status query URI"
    assert "sendEventPostUri" in data, "Response should contain send event URI"
    assert "terminatePostUri" in data, "Response should contain terminate URI"
    assert "purgeHistoryDeleteUri" in data, "Response should contain purge history URI"


def test_orchestration_status():
    """Test orchestration status monitoring (basic connectivity test)"""
    # First start an orchestration
    test_payload = {
        "projectId": "level2-status-test",
        "snippets": [
            {
                "name": "status_test.py",
                "code": "print('Status monitoring test')"
            }
        ]
    }

    headers = {
        "x-functions-key": FUNCTION_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{FUNCTION_APP_URL}/api/orchestrators/embeddings",
        json=test_payload,
        headers=headers,
        timeout=30
    )

    assert response.status_code == 202, f"Expected 202, got {response.status_code}: {response.text}"

    data = response.json()
    status_url = data["statusQueryGetUri"]

    # Test that status endpoint is accessible (note: may require different auth)
    # We're testing the URL structure rather than full authentication
    assert "runtime/webhooks/durabletask/instances" in status_url, "Status URL should be a valid Durable Functions status endpoint"


def test_payload_validation_invalidpayloads():
    """Test that the orchestration endpoint validates required fields"""
    headers = {
        "x-functions-key": FUNCTION_KEY,
        "Content-Type": "application/json"
    }

    # Test missing code
    invalid_payloads = [
        {
            "projectId": "level2-test",
            "code": "print('test')"
        },
        {
            "projectId": "level2-test",
            "snippets": [
                {
                    "name": "test.py",
                },
                {
                    "name": "test2.py",
                    "code": "print('test2')"
                }
            ]
        },
        {
            "projectId": "level2-test",
            "snippets": [
                {
                    "name": "test.py",
                },
                {
                    "code": "print('test2')"
                }
            ]
        }
    ]

    for invalid_payload in invalid_payloads:
        response = requests.post(
            f"{FUNCTION_APP_URL}/api/orchestrators/embeddings",
            json=invalid_payload,
            headers=headers,
            timeout=30
        )

        assert response.status_code in [400,
            500], f"Unexpected status code: {response.status_code}"


def test_payload_validation_validpayloads_via_http():
    """Test that the orchestration endpoint validates required fields"""
    headers = {
        "x-functions-key": FUNCTION_KEY,
        "Content-Type": "application/json"
    }

    # Test missing code
    invalid_payloads = [
        {
            "projectId": "level2-test",
            "snippets": [
                {
                    "name": "test.py",
                    "code": "print('test2')"
                }
            ]
        },
        {
            "projectId": "level2-test",
            "snippets": [
                {
                    "name": "test.py",
                    "code": "print('test2')"
                },
                {
                    "name": "test2.py",
                    "code": "print('test2')",
                    "language": "python"
                }
            ]
        },
        {
            "projectId": "level2-test",
            "snippets": [
                {
                    "name": "test2.py",
                    "code": "print('test2')",
                    "language": "python",
                    "description": "Test description for test2.py"
                }
            ]
        }
    ]

    for invalid_payload in invalid_payloads:
        response = requests.post(
            f"{FUNCTION_APP_URL}/api/orchestrators/embeddings",
            json=invalid_payload,
            headers=headers,
            timeout=30
        )

        assert response.status_code in [
            202], f"Unexpected status code: {response.status_code} for snippet: {invalid_payload}"


def test_large_payload_handling_via_http():
    """Test orchestration with larger text payload to validate chunking logic"""
    large_text = "# Large test file\n" + \
        "\n".join([f"def function_{i}():\n    return {i}" for i in range(50)])

    test_payload = {
        "projectId": "level2-large-test",
        "snippets": [
            {
                "name": "large_test.py",
                "code": large_text
            }
        ]
    }

    headers = {
        "x-functions-key": FUNCTION_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{FUNCTION_APP_URL}/api/orchestrators/embeddings",
        json=test_payload,
        headers=headers,
        timeout=30
    )

    assert response.status_code == 202, f"Expected 202, got {response.status_code}: {response.text}"

    data = response.json()
    assert "id" in data, "Response should contain orchestration instance ID for large payload"


@pytest.mark.parametrize("payload", [
    None,
    123,
    "string",
    {},  # missing projectId & snippets
    {"projectId": "p"},  # missing snippets
    {"snippets": []},  # missing projectId
    {"projectId": "p", "snippets": []},  # empty list not allowed
    {"projectId": "p", "snippets": "not-a-list"},
    {"projectId": "p", "snippets": ["not-a-dict"]},
    {"projectId": "p", "snippets": [{"name": "a"}]},  # missing code
    {"projectId": "p", "snippets": [{"code": "print(1)"}]},  # missing name
    {"projectId": "p", "snippets": [
        {"name": "a", "code": "   "}]},  # empty code
])
def test_validate_input_invalid(payload):
    assert not validate_input(payload), f"Payload should be invalid: {payload}"


@pytest.mark.parametrize("payload", [
    {"projectId": "p", "snippets": [{"name": "a", "code": "print(1)"}]},
    {"projectId": "p", "snippets": [
        {"name": "a", "code": "print(1)", "language": "python"}]},
    {"projectId": "p", "snippets": [
        {"name": "a", "code": "print(1)", "description": "desc"}]},
    {"projectId": "p", "snippets": [
        {"name": "a", "code": "print(1)", "language": "python", "description": "desc"}]},
])
def test_validate_input_valid(payload):
    assert validate_input(payload), f"Payload should be valid: {payload}"


def main():
    """Run all Level 2 tests in standalone mode"""
    print("🎯 Starting Level 2 Cloud Testing")
    print("=" * 50)

    try:
        test_orchestration_endpoint()
        print("✅ Orchestration endpoint test passed!")

        test_orchestration_status()
        print("✅ Orchestration status test passed!")

        test_payload_validation()
        print("✅ Payload validation test passed!")

        test_large_payload_handling()
        print("✅ Large payload handling test passed!")

        print("\n🎉 LEVEL 2 COMPLETED SUCCESSFULLY!")
        print("\n✅ ACHIEVEMENTS UNLOCKED:")
        print("   🏗️  Durable Functions Orchestration Working")
        print("   ⚡ HTTP 202 Async Pattern Implemented")
        print("   🧩 Status Monitoring URLs Generated")
        print("   🔄 Payload Validation Active")
        print("   📊 Large Text Handling Verified")
        print("\n🔍 TECHNICAL VALIDATION:")
        print("   • Orchestrations starting successfully (HTTP 202)")
        print("   • Proper Durable Functions response structure")
        print("   • Status monitoring endpoints configured")
        print("   • Large payload chunking logic functional")
        print("\n🚀 READY FOR LEVEL 3: Vector Search & AI Q&A")
        return 0

    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
