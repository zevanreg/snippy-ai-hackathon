import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

import function_app
from activities import blob_ops, cosmos_ops

@pytest.mark.asyncio
async def test_upload_raw_code_activity():
    """
    Test the upload_raw_code_activity function.
    Verifies that the function correctly uploads code to blob storage.
    """
    test_payload = {
        "code": "def test_function():\n    return 'Hello, World!'",
        "project_id": "test-project",
        "name": "test-snippet"
    }
    
    test_blob_url = "https://test-storage.blob.core.windows.net/snippet-backups/test-project/test-snippet.txt"
    
    with patch.object(blob_ops, 'upload_raw_code', new_callable=AsyncMock) as mock_upload:
        mock_upload.return_value = test_blob_url
        
        result = await function_app.upload_raw_code_activity(test_payload)
        
        assert result == test_blob_url
        
        mock_upload.assert_called_once_with(
            test_payload["code"],
            test_payload["project_id"],
            test_payload["name"]
        )

@pytest.mark.asyncio
async def test_generate_embedding_activity():
    """
    Test the generate_embedding_activity function.
    Verifies that the function correctly generates an embedding for code.
    """
    test_code = "def test_function():\n    return 'Hello, World!'"
    test_embeddings = json.dumps({
        "count": 1,
        "data": [0.1, 0.2, 0.3]
    })
    
    result = await function_app.generate_embedding_activity(test_code, test_embeddings)
    
    assert result == [0.1, 0.2, 0.3]

@pytest.mark.asyncio
async def test_upsert_document_activity():
    """
    Test the upsert_document_activity function.
    Verifies that the function correctly upserts a document to Cosmos DB.
    """
    test_payload = {
        "name": "test-snippet",
        "project_id": "test-project",
        "code": "def test_function():\n    return 'Hello, World!'",
        "blob_url": "https://test-storage.blob.core.windows.net/snippet-backups/test-project/test-snippet.txt",
        "embedding": [0.1, 0.2, 0.3]
    }
    
    test_result = {
        "id": "test-snippet",
        "projectId": "test-project",
        "code": "def test_function():\n    return 'Hello, World!'",
        "blobUrl": "https://test-storage.blob.core.windows.net/snippet-backups/test-project/test-snippet.txt",
        "embedding": [0.1, 0.2, 0.3]
    }
    
    with patch.object(cosmos_ops, 'upsert_document', new_callable=AsyncMock) as mock_upsert:
        mock_upsert.return_value = test_result
        
        result = await function_app.upsert_document_activity(test_payload)
        
        assert result == test_result
        
        mock_upsert.assert_called_once_with(
            test_payload["name"],
            test_payload["project_id"],
            test_payload["code"],
            test_payload["blob_url"],
            test_payload["embedding"]
        )
