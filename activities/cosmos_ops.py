import os
import logging
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey

async def upsert_document(name: str, project_id: str, code: str, blob_url: str, embedding: list) -> dict:
    """
    Upserts a document into Cosmos DB with vector embedding.
    
    Args:
        name: The name of the snippet (used as id)
        project_id: The project ID (used as partition key)
        code: The code content
        blob_url: The URL of the blob in storage
        embedding: The embedding vector from OpenAI
        
    Returns:
        The created/updated document
    """
    try:
        cosmos_conn = os.environ["COSMOS_CONN"]
        client = CosmosClient.from_connection_string(cosmos_conn)
        
        database_name = "dev-snippet-db"
        database = client.get_database_client(database_name)
        
        container_name = "code-snippets"
        container = database.get_container_client(container_name)
        
        document = {
            "id": name,
            "projectId": project_id,
            "code": code,
            "blobUrl": blob_url,
            "embedding": embedding
        }
        
        result = await container.upsert_item(document)
        logging.info(f"Upserted document with id {name}")
        
        return result
    except Exception as e:
        logging.error(f"Error upserting document: {str(e)}")
        raise

async def get_snippet_by_id(name: str) -> dict:
    """
    Gets a snippet from Cosmos DB by id.
    
    Args:
        name: The name (id) of the snippet to retrieve
        
    Returns:
        The retrieved document or None if not found
    """
    try:
        cosmos_conn = os.environ["COSMOS_CONN"]
        client = CosmosClient.from_connection_string(cosmos_conn)
        
        database_name = "dev-snippet-db"
        database = client.get_database_client(database_name)
        
        container_name = "code-snippets"
        container = database.get_container_client(container_name)
        
        query = "SELECT * FROM c WHERE c.id = @id"
        parameters = [{"name": "@id", "value": name}]
        
        items = []
        async for item in container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ):
            items.append(item)
        
        if not items:
            return None
        
        return items[0]
    except Exception as e:
        logging.error(f"Error retrieving snippet: {str(e)}")
        raise

async def search_similar_snippets(embedding: list, top_k: int = 5) -> list:
    """
    Searches for similar snippets using vector search.
    
    Args:
        embedding: The embedding vector to search with
        top_k: The number of results to return
        
    Returns:
        List of similar snippets
    """
    try:
        cosmos_conn = os.environ["COSMOS_CONN"]
        client = CosmosClient.from_connection_string(cosmos_conn)
        
        database_name = "dev-snippet-db"
        database = client.get_database_client(database_name)
        
        container_name = "code-snippets"
        container = database.get_container_client(container_name)
        
        query = """
        SELECT TOP @top_k c.id, c.projectId, c.code, c.blobUrl,
               VectorDistance(c.embedding, @embedding) as distance
        FROM c
        ORDER BY VectorDistance(c.embedding, @embedding)
        """
        
        parameters = [
            {"name": "@embedding", "value": embedding},
            {"name": "@top_k", "value": top_k}
        ]
        
        items = []
        async for item in container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ):
            items.append(item)
        
        return items
    except Exception as e:
        logging.error(f"Error searching similar snippets: {str(e)}")
        raise
