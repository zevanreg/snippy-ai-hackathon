import json
import pytest
import azure.functions as func
from unittest.mock import patch, MagicMock, AsyncMock

import function_app
from activities import cosmos_ops
from agents import deep_research, code_style

@pytest.mark.asyncio
async def test_get_snippet():
    """
    Test the get_snippet function.
    Verifies that the function correctly retrieves a snippet by name.
    """
    test_snippet = {
        "id": "test-snippet",
        "projectId": "test-project",
        "code": "def test_function():\n    return 'Hello, World!'",
        "blobUrl": "https://test-storage.blob.core.windows.net/snippet-backups/test-project/test-snippet.txt",
        "embedding": [0.1, 0.2, 0.3]
    }
    
    with patch.object(cosmos_ops, 'get_snippet_by_id', new_callable=AsyncMock) as mock_get_snippet:
        mock_get_snippet.return_value = test_snippet
        
        req = func.HttpRequest(
            method='GET',
            body=None,
            url='/api/snippets/test-snippet',
            route_params={'name': 'test-snippet'}
        )
        
        response = await function_app.get_snippet(req)
        
        assert response.status_code == 200
        assert json.loads(response.get_body()) == test_snippet
        
        mock_get_snippet.assert_called_once_with('test-snippet')

@pytest.mark.asyncio
async def test_get_snippet_not_found():
    """
    Test the get_snippet function when the snippet is not found.
    Verifies that the function returns a 404 response.
    """
    with patch.object(cosmos_ops, 'get_snippet_by_id', new_callable=AsyncMock) as mock_get_snippet:
        mock_get_snippet.return_value = None
        
        req = func.HttpRequest(
            method='GET',
            body=None,
            url='/api/snippets/nonexistent-snippet',
            route_params={'name': 'nonexistent-snippet'}
        )
        
        response = await function_app.get_snippet(req)
        
        assert response.status_code == 404
        assert 'not found' in json.loads(response.get_body())['error']
        
        mock_get_snippet.assert_called_once_with('nonexistent-snippet')

@pytest.mark.asyncio
async def test_deep_research_function():
    """
    Test the deep_research_function.
    Verifies that the function correctly performs deep research on a snippet.
    """
    test_snippet = {
        "id": "test-snippet",
        "projectId": "test-project",
        "code": "def test_function():\n    return 'Hello, World!'",
        "blobUrl": "https://test-storage.blob.core.windows.net/snippet-backups/test-project/test-snippet.txt",
        "embedding": [0.1, 0.2, 0.3]
    }
    
    test_similar_snippets = [
        {
            "id": "similar-snippet",
            "projectId": "test-project",
            "code": "def similar_function():\n    return 'Similar!'",
            "distance": 0.5
        }
    ]
    
    test_research_results = "This is a simple function that returns 'Hello, World!'."
    
    with patch.object(cosmos_ops, 'get_snippet_by_id', new_callable=AsyncMock) as mock_get_snippet:
        mock_get_snippet.return_value = test_snippet
        
        with patch.object(cosmos_ops, 'search_similar_snippets', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = test_similar_snippets
            
            with patch.object(deep_research, 'perform_deep_research', new_callable=AsyncMock) as mock_research:
                mock_research.return_value = test_research_results
                
                req = func.HttpRequest(
                    method='POST',
                    body=None,
                    url='/api/snippets/test-snippet/research',
                    route_params={'name': 'test-snippet'}
                )
                
                response = await function_app.deep_research_function(req)
                
                assert response.status_code == 200
                assert json.loads(response.get_body())['research'] == test_research_results
                
                mock_get_snippet.assert_called_once_with('test-snippet')
                mock_search.assert_called_once_with(test_snippet['embedding'])
                mock_research.assert_called_once_with(test_snippet['code'], test_similar_snippets)

@pytest.mark.asyncio
async def test_create_code_style_function():
    """
    Test the create_code_style_function.
    Verifies that the function correctly generates a code style guide based on a snippet.
    """
    test_snippet = {
        "id": "test-snippet",
        "projectId": "test-project",
        "code": "def test_function():\n    return 'Hello, World!'",
        "blobUrl": "https://test-storage.blob.core.windows.net/snippet-backups/test-project/test-snippet.txt",
        "embedding": [0.1, 0.2, 0.3]
    }
    
    test_similar_snippets = [
        {
            "id": "similar-snippet",
            "projectId": "test-project",
            "code": "def similar_function():\n    return 'Similar!'",
            "distance": 0.5
        }
    ]
    
    test_style_guide = "# Python Style Guide\n\n1. Use 4 spaces for indentation."
    
    with patch.object(cosmos_ops, 'get_snippet_by_id', new_callable=AsyncMock) as mock_get_snippet:
        mock_get_snippet.return_value = test_snippet
        
        with patch.object(cosmos_ops, 'search_similar_snippets', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = test_similar_snippets
            
            with patch.object(code_style, 'generate_code_style', new_callable=AsyncMock) as mock_style:
                mock_style.return_value = test_style_guide
                
                req = func.HttpRequest(
                    method='POST',
                    body=None,
                    url='/api/snippets/test-snippet/code-style',
                    route_params={'name': 'test-snippet'}
                )
                
                response = await function_app.create_code_style_function(req)
                
                assert response.status_code == 200
                assert json.loads(response.get_body())['styleGuide'] == test_style_guide
                
                mock_get_snippet.assert_called_once_with('test-snippet')
                mock_search.assert_called_once_with(test_snippet['embedding'])
                mock_style.assert_called_once_with(test_snippet['code'], test_similar_snippets)
