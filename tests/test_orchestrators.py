import json
import pytest
import azure.functions as func
import azure.durable_functions as df
from azure.functions.durable_functions import DurableOrchestrationClient
from unittest.mock import patch, MagicMock

from orchestrators import save_snippet_orchestrator

@pytest.mark.asyncio
async def test_save_snippet_orchestrator():
    """
    Test the save_snippet_orchestrator function.
    Verifies the fan-out/fan-in pattern and the correct handling of results.
    """
    mock_context = MagicMock(spec=df.DurableOrchestrationContext)
    
    test_data = {
        "name": "test-snippet",
        "projectId": "test-project",
        "code": "def test_function():\n    return 'Hello, World!'"
    }
    
    mock_context.get_input.return_value = test_data
    
    mock_blob_url = "https://test-storage.blob.core.windows.net/snippet-backups/test-project/test-snippet.txt"
    mock_embedding = [0.1, 0.2, 0.3]
    
    mock_context.task_all.return_value = [mock_blob_url, mock_embedding]
    
    mock_document = {
        "id": "test-snippet",
        "projectId": "test-project",
        "status": "completed"
    }
    mock_context.call_activity.return_value = mock_document
    
    result = await save_snippet_orchestrator(mock_context)
    
    mock_context.call_activity.assert_any_call("upload_raw_code", {
        "code": test_data["code"],
        "project_id": test_data["projectId"],
        "name": test_data["name"]
    })
    
    mock_context.call_activity.assert_any_call("generate_embedding", test_data["code"])
    
    assert mock_context.task_all.call_count == 1
    
    mock_context.call_activity.assert_any_call("upsert_document", {
        "name": test_data["name"],
        "project_id": test_data["projectId"],
        "code": test_data["code"],
        "blob_url": mock_blob_url,
        "embedding": mock_embedding
    })
    
    assert result == {
        "id": "test-snippet",
        "projectId": "test-project",
        "status": "completed"
    }
