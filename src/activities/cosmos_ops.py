import os
import logging
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError

# Constants for Cosmos DB configuration
COSMOS_DATABASE_NAME = os.environ.get("COSMOS_DATABASE_NAME", "dev-snippet-db")
COSMOS_CONTAINER_NAME = os.environ.get("COSMOS_CONTAINER_NAME", "code-snippets")

async def get_container():
    """
    Gets or creates the Cosmos DB container with proper partition key configuration.
    
    Returns:
        The container client
    """
    client = CosmosClient.from_connection_string(os.environ["COSMOS_CONN"])
    database = await client.create_database_if_not_exists(COSMOS_DATABASE_NAME)
    container = await database.create_container_if_not_exists(
        id=COSMOS_CONTAINER_NAME,
        partition_key=PartitionKey(path="/name")
    )
    return container

async def upsert_document(name: str, project_id: str, code: str, embedding: list) -> dict:
    """
    Upserts a document into Cosmos DB.
    
    Args:
        name: The name of the snippet (used as id and partition key)
        project_id: The project ID
        code: The code content
        embedding: The embedding vector from Azure OpenAI
        
    Returns:
        The created/updated document
    """
    try:
        container = await get_container()
        
        # Prepare the document
        document = {
            "id": name,
            "name": name,  # This field is used for partition key
            "projectId": project_id,
            "code": code,
            "type": "code-snippet",
            "embedding": embedding  # Store the embedding vector
        }
        
        # Upsert the document using the name as partition key
        result = await container.upsert_item(
            body=document
        )
        
        logging.info(f"Successfully upserted document with id '{name}' in project '{project_id}'")
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
        container = await get_container()
        
        try:
            result = await container.read_item(
                item=name,
                partition_key=name
            )
            logging.info(f"Successfully retrieved snippet with id '{name}'")
            return result
        except CosmosResourceNotFoundError:
            logging.info(f"No snippet found with id '{name}'")
            return None
                
    except Exception as e:
        logging.error(f"Error retrieving snippet: {str(e)}")
        raise
