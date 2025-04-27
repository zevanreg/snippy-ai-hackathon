import json
import logging
import os
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from azure.ai.inference.aio import EmbeddingsClient
from data import cosmos_ops

# Configure logging for this module
logger = logging.getLogger(__name__)

# Reduce Azure SDK logging
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("azure.core").setLevel(logging.WARNING)
logging.getLogger("azure.ai.projects").setLevel(logging.WARNING)

async def vector_search(query: str, k: int = 30, project_id: str = "default-project") -> str:
    """
    Performs vector similarity search on code snippets using Azure AI Inference via AI Project Client.
    
    This tool obtains an authenticated embeddings client via the AI Project Client,
    generates embeddings for the query, and then queries Cosmos DB's vector index
    for similar snippets.
    
    Args:
        query: The search query text (can be plain language or code fragment).
        k: Number of results to return (default: 30).
        project_id: The project ID to search within (default: "default-project").
        
    Returns:
        JSON string containing matching snippets with their IDs, code, and score:
        [
            {"id": "snippet-1", "code": "...", "score": 0.95},
            {"id": "snippet-2", "code": "...", "score": 0.92},
            ...
        ]
        
    Raises:
        Exception: If obtaining clients, embedding generation, or database query fails.
    """
    project_connection_string = os.environ.get("PROJECT_CONNECTION_STRING")
    model_deployment_name = os.environ.get("EMBEDDING_MODEL_DEPLOYMENT_NAME")

    if not project_connection_string or not model_deployment_name:
        raise ValueError("Required environment variables not configured.")

    try:
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient.from_connection_string(
                credential=credential,
                conn_str=project_connection_string,
            ) as project_client:
                async with await project_client.inference.get_embeddings_client() as embeddings_client:
                    # Generate embedding for the query
                    response = await embeddings_client.embed(
                        model=model_deployment_name,
                        input=[query]
                    )

                    if not response.data or not response.data[0].embedding:
                        raise ValueError("Failed to generate embedding.")

                    query_vector = response.data[0].embedding

                    # Query Cosmos DB
                    results = await cosmos_ops.query_similar_snippets(
                        query_vector=query_vector,
                        project_id=project_id,
                        k=k
                    )

                    return json.dumps(results)

    except Exception as e:
        logger.error("Vector search failed: %s", str(e), exc_info=True)
        return json.dumps({"error": str(e)})
    finally:
        await cosmos_ops.close_connections() 