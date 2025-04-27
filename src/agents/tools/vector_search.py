# Module for vector similarity search tool in Azure AI Projects:
# - Authenticates via Azure DefaultAzureCredential
# - Generates text embeddings for the query using Azure AI Inference
# - Queries Cosmos DB vector index for similar code snippets
# - Returns results as a JSON string
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

# Performs vector similarity search on code snippets
# Args:
#     query: The search query text (plain language or code fragment)
#     k: Number of top matches to return
#     project_id: The project ID to scope the search
# Returns:
#     JSON string of matching snippets with their IDs, code, and similarity scores
async def vector_search(query: str, k: int = 30, project_id: str = "default-project") -> str:
    # Retrieve required environment variables for authentication and model
    project_connection_string = os.environ.get("PROJECT_CONNECTION_STRING")
    model_deployment_name = os.environ.get("EMBEDDING_MODEL_DEPLOYMENT_NAME")

    # Validate configuration
    if not project_connection_string or not model_deployment_name:
        raise ValueError("Required environment variables not configured.")

    try:
        # Authenticate with Azure using DefaultAzureCredential
        async with DefaultAzureCredential() as credential:
            # Connect to the AI Project client using the connection string
            async with AIProjectClient.from_connection_string(
                credential=credential,
                conn_str=project_connection_string,
            ) as project_client:
                # Create an embeddings client from the AI project
                async with await project_client.inference.get_embeddings_client() as embeddings_client:
                    # Generate embeddings for the input query
                    response = await embeddings_client.embed(
                        model=model_deployment_name,
                        input=[query]
                    )

                    # Ensure the embedding was generated successfully
                    if not response.data or not response.data[0].embedding:
                        raise ValueError("Failed to generate embedding.")

                    # Extract the embedding vector
                    query_vector = response.data[0].embedding

                    # Perform vector search in Cosmos DB with the generated embedding
                    results = await cosmos_ops.query_similar_snippets(
                        query_vector=query_vector,
                        project_id=project_id,
                        k=k
                    )

                    # Return the search results as a JSON string
                    return json.dumps(results)

    except Exception as e:
        # Log any errors and return an error payload
        logger.error("Vector search failed: %s", str(e), exc_info=True)
        return json.dumps({"error": str(e)})
    finally:
        # Close Cosmos DB connections to clean up resources
        await cosmos_ops.close_connections() 