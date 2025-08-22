#!/usr/bin/env python3
"""
Level 4 Cloud Testing - Event-driven Ingestion + Observability

This test suite validates the event-driven ingestion system:
- Blob trigger activation on file upload
- Content validation and filtering  
- Automatic orchestration startup
- Error handling and resilience
- Observability and monitoring

Production deployment testing with Azure Storage.
"""
import os
import sys
import time
import json
import tempfile
import logging
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import requests
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError
import uuid

# FUNCTION_APP_URL = os.getenv("FUNCTION_APP_URL", "https://your-function-app.azurewebsites.net")
FUNCTION_APP_URL = "http://localhost:7071"
FUNCTION_KEY = os.getenv("FUNCTION_KEY", "your-function-key-here")
STORAGE_CONNECTION_STRING = os.getenv("STORAGE_CONNECTION_STRING", "your-storage-connection-string-here")
CONTAINER_NAME = "snippet-inputs"
PROJECT_NAME = f"test-project-{uuid.uuid4().hex[:8]}"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)



def _make_request(method: str, endpoint: str, **kwargs) -> requests.Response:
    """Make HTTP request to function app with authentication."""
    url = f"{FUNCTION_APP_URL}/api/{endpoint}"
    headers = kwargs.pop('headers', {})
    headers['x-functions-key'] = FUNCTION_KEY
    
    response = requests.request(method, url, headers=headers, **kwargs)
    logger.info(f"{method} {endpoint} -> {response.status_code}")
    return response


def get_storage_client():
    return BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)


def test_1_health_check():
    """Test 1: Verify function app is healthy."""
    logger.info("🔍 Test 1: Health check")
    
    try:
        response = _make_request("GET", "health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        
        result = response.json()
        assert result["status"] in ["healthy", "ok"], f"Health status not healthy: {result}"
        
        logger.info("✅ Test 1 PASSED: Function app is healthy")
        
    except Exception as e:
        logger.error(f"❌ Test 1 FAILED: {str(e)}")
        pytest.fail(f"Health check failed: {str(e)}")

def test_2_storage_connection():
    """Test 2: Verify storage connection and container setup."""
    try:
        logger.info("🔍 Test 2: Storage connection and container setup")
        
        storage_client = get_storage_client()
        container_client = storage_client.get_container_client(CONTAINER_NAME)
        assert container_client.exists(), f"Container '{CONTAINER_NAME}' does not exist"
        
        container_client.get_container_properties()
        logger.info(f"Container '{CONTAINER_NAME}' exists")
        
        logger.info("✅ Test 2 PASSED: Storage connection working")        
        
    except Exception as e:
        logger.error(f"❌ Test 2 FAILED: {e}")
        pytest.fail(f"Storage connection test failed: {e}")

def test_3_file_upload_and_processing() -> bool:
    """Test 3: Upload files and verify they trigger ingestion."""
    try:
        logger.info("🔍 Test 3: File upload and automatic processing")
        
        # Test files to upload
        # Use a run-scoped unique suffix to avoid name collisions across test runs / parallel executions.
        run_suffix = uuid.uuid4().hex[:6]
        test_files = [
            (f"hello_world_{run_suffix}.py", '''def hello_world():
"""A simple greeting function."""
print("Hello, World!")
return "success"
'''),
            (f"api_docs_{run_suffix}.md", '''# API Documentation

## Authentication
Use Bearer tokens for API authentication.

```python
headers = {"Authorization": "Bearer <token>"}
response = requests.get("/api/data", headers=headers)
```
'''),
            (f"config_{run_suffix}.json", '''{
"name": "test-config",
"version": "1.0.0",
"settings": {
    "debug": true,
    "timeout": 30
}
}
''')
        ]
        
        container_client = get_storage_client().get_container_client(CONTAINER_NAME)
        successful_uploads = 0

        for filename, content in test_files:
            try:
                # Upload file to trigger blob ingestion
                blob_client = container_client.get_blob_client(filename)
                blob_client.upload_blob(content, overwrite=True)
                successful_uploads += 1
                logger.info(f"📁 Uploaded {filename}")
                
                # Small delay between uploads to prevent overwhelming
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to upload {filename}: {e}")
        
        assert successful_uploads == len(test_files), (
            f"Only {successful_uploads} out of {len(test_files)} files uploaded successfully"
        )

        if successful_uploads == len(test_files):
            logger.info(
                f"✅ Test 3 PASSED: Successfully uploaded {successful_uploads}/{len(test_files)} files"
            )
        else:
            logger.error("❌ Test 3 FAILED: No files uploaded successfully")

        # Time-based retry loop: allow up to 30s for all files to be processed
        deadline_sec = 30
        poll_interval = 3
        start_time = time.time()
        remaining = {fname for fname, _ in test_files}

        while remaining and (time.time() - start_time) < deadline_sec:
            to_remove = set()
            for filename in list(remaining):
                response = _make_request("GET", f"snippets/{filename}")
                if response.status_code == 200:
                    data = response.json()
                    if data:  # Found at least one snippet
                        logger.info(f"✅ Snippets available for {filename}")
                        to_remove.add(filename)
                else:
                    logger.debug(
                        f"Non-200 while checking {filename}: {response.status_code}"
                    )
            remaining -= to_remove
            if remaining:
                logger.info(
                    f"Waiting for snippets... {len(remaining)} file(s) still pending: {sorted(remaining)}"
                )
                time.sleep(poll_interval)

        if remaining:
            logger.error(
                f"❌ Test 3 FAILED: No snippets found for files: {sorted(remaining)} within {deadline_sec}s"
            )
            pytest.fail(
                f"❌ Test 3 FAILED: No snippets found for files: {sorted(remaining)} within {deadline_sec}s"
            )
        else:
            logger.info("✅ Test 3 PASSED: Snippets found for all uploaded files")

    except Exception as e:
        logger.error(f"❌ Test 3 FAILED: {e}")
        pytest.fail(f"File upload test failed: {e}")


def main():
    """Run Level 4 cloud tests."""
    logger.info("🚀 Starting Level 4 Cloud Testing")
    test_1_health_check()
    test_2_storage_connection()
    test_3_file_upload_and_processing()

if __name__ == "__main__":
    main()
