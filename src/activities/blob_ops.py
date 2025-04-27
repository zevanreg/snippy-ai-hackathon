import os
import logging
from azure.storage.blob.aio import BlobServiceClient

# Constants for Blob Storage configuration
BLOB_CONTAINER_NAME = os.environ.get("BLOB_CONTAINER_NAME", "snippet-backups")

async def upload_raw_code(code: str, project_id: str, name: str) -> str:
    """
    Uploads raw code to Azure Blob Storage.
    
    Args:
        code: The code content to upload
        project_id: The project ID to use in the blob path
        name: The name of the snippet
        
    Returns:
        The URL of the uploaded blob
    """
    try:
        connection_string = os.environ["AzureWebJobsStorage"]
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
        
        try:
            await container_client.create_container()
            logging.info(f"Container '{BLOB_CONTAINER_NAME}' created")
        except Exception as e:
            logging.info(f"Container creation: {str(e)}")
        
        blob_path = f"{project_id}/{name}.txt"
        blob_client = container_client.get_blob_client(blob_path)
        await blob_client.upload_blob(code, overwrite=True)
        
        blob_url = blob_client.url
        logging.info(f"Uploaded blob to {blob_url}")
        
        return blob_url
    except Exception as e:
        logging.error(f"Error uploading blob: {str(e)}")
        raise
