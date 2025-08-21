"""Timer-based ingestion blueprint (Level 4 alternative).

- Timer trigger polls blob storage every minute for new files
- Processes files and removes them after successful ingestion
- Provides event-driven behavior without blob trigger limitations
"""
from __future__ import annotations

import logging
import os
import json
from datetime import datetime

import azure.functions as func
import azure.durable_functions as df
from azure.storage.blob import BlobServiceClient, BlobClient
import azurefunctions.extensions.bindings.blob as blob

bp = func.Blueprint()

INGESTION_CONTAINER = os.environ.get("INGESTION_CONTAINER", "ingestion")
MAX_BLOB_MB = int(os.environ.get("MAX_BLOB_MB", "2"))
STORAGE_CONNECTION = os.environ.get("AzureWebJobsStorage")


@bp.blob_trigger(arg_name="myblob", 
                  path=INGESTION_CONTAINER,
                  connection="AzureWebJobsStorage")
@bp.durable_client_input(client_name="starter")
async def poll_ingestion_container(myblob: blob.BlobClient, starter: df.DurableOrchestrationClient) -> None:
    """Poll blob storage for new files to ingest."""
    logging.info("Blob trigger fired for blob: %s", myblob.blob_name)

    try:
        await process_blob(myblob.blob_name, myblob, starter)
    except Exception as e:
        logging.error("Failed to process blob %s: %s", myblob.name, e)


# async def process_blob(blob_name: str, container_client, starter: df.DurableOrchestrationClient) -> None:
async def process_blob(blob_name: str, blob_client : BlobClient, starter: df.DurableOrchestrationClient) -> None:
    """Process a single blob file."""
    try:
        logging.info(f"Processing blob: {blob_name}")
        blob_data = blob_client.download_blob()
        content = blob_data.readall()
        logging.info(f"Blob {blob_name} downloaded successfully")
        
        # Check blob size
        blob_length = len(content)
        size_mb = blob_length / (1024 * 1024)
        if size_mb > MAX_BLOB_MB:
            logging.warning("Skipping blob %s: size %.2fMB > limit %dMB", blob_name, size_mb, MAX_BLOB_MB)
            # Delete oversized file
            blob_client.delete_blob()
            return

        # Check file type
        if not blob_name.lower().endswith((".md", ".txt", ".py", ".js", ".ts", ".java", ".cpp", ".c", ".cs", ".go", ".rs", ".rb", ".php", ".sh", ".sql", ".json", ".xml", ".yaml", ".yml")):
            logging.info("Skipping non-supported file: %s", blob_name)
            # Delete unsupported file
            blob_client.delete_blob()
            return

        # Text extraction with encoding handling
        try:
            if isinstance(content, bytes):
                try:
                    text = content.decode("utf-8")
                except UnicodeDecodeError:
                    text = content.decode("utf-8", errors="ignore")
                    logging.warning("Unicode decode errors in %s, using error-ignore mode", blob_name)
            else:
                text = str(content)
        except Exception as e:
            logging.error("Failed to decode content from %s: %s", blob_name, e)
            # Delete unreadable file
            blob_client.delete_blob()
            return

        if not text.strip():
            logging.warning("Skipping empty file: %s", blob_name)
            # Delete empty file
            blob_client.delete_blob()
            return

        payload = {
            "projectId": os.environ.get("DEFAULT_PROJECT_ID", "default-project"), 
            "name": blob_name, 
            "text": text
        }

        # Start orchestration
        try:
            instance_id = await starter.start_new("embeddings_orchestrator", None, payload)
            logging.info("Ingestion started orchestration id=%s for %s", instance_id, blob_name)
            
            # Delete successfully processed file
            blob_client.delete_blob()
            logging.info("Deleted processed file: %s", blob_name)
            
        except Exception as e:
            logging.error("Failed to start orchestration for %s: %s", blob_name, e)
            raise

    except Exception as e:
        logging.error("Processing failed for %s: %s", blob_name, e, exc_info=True)
        # Don't delete file on processing errors - will retry next cycle


@bp.route(route="ingestion/upload", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
async def http_upload_for_ingestion(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP endpoint for file upload that saves to blob storage for timer processing."""
    logging.info("Upload endpoint called")
    
    if not STORAGE_CONNECTION:
        logging.error("Storage connection not configured")
        return func.HttpResponse(
            body=json.dumps({"error": "Storage not configured"}),
            mimetype="application/json",
            status_code=500
        )
    
    try:
        # Parse request
        req_body = req.get_json()
        if not req_body:
            logging.error("No JSON body in request")
            return func.HttpResponse(
                body=json.dumps({"error": "Request body is required"}),
                mimetype="application/json",
                status_code=400
            )

        filename = req_body.get("filename")
        content = req_body.get("content")

        if not filename or not content:
            logging.error("Missing filename or content")
            return func.HttpResponse(
                body=json.dumps({"error": "filename and content are required"}),
                mimetype="application/json",
                status_code=400
            )

        logging.info(f"Uploading file {filename} to container {INGESTION_CONTAINER}")
        
        # Upload to blob storage for timer processing
        blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION)
        blob_client = blob_service_client.get_blob_client(
            container=INGESTION_CONTAINER,
            blob=filename
        )
        
        blob_client.upload_blob(content, overwrite=True)
        logging.info(f"Successfully uploaded {filename}")
        
        return func.HttpResponse(
            body=json.dumps({
                "success": True,
                "message": f"File {filename} uploaded and queued for processing",
                "filename": filename
            }),
            mimetype="application/json",
            status_code=202
        )
        
    except Exception as e:
        logging.error("Upload failed: %s", e, exc_info=True)
        return func.HttpResponse(
            body=json.dumps({"error": f"Upload failed: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )
