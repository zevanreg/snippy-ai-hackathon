"""Timer-based ingestion blueprint (Level 4 alternative).

- Timer trigger polls blob storage every minute for new files
- Processes files and removes them after successful ingestion
- Provides event-driven behavior without blob trigger limitations
"""
from __future__ import annotations

import asyncio
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


@bp.blob_trigger(arg_name="blob_client", 
                  path=INGESTION_CONTAINER,
                  connection="AzureWebJobsStorage")
@bp.durable_client_input(client_name="df_client")
async def monitor_ingestion_container(blob_client: blob.BlobClient, df_client: df.DurableOrchestrationClient):
    """Poll blob storage for new files to ingest."""
    #TODO: Implement processing of blob
    logging.error("Ingestion not implemented yet")


async def process_blob(blob_name: str, blob_client : BlobClient, df_client: df.DurableOrchestrationClient):
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
            "snippets": [
                {
                    "name": blob_name, 
                    "code": text
                }
            ]
        }

        # Orchestration startup with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                instance_id = await df_client.start_new("embeddings_orchestrator", None, payload)
                logging.info("Ingestion started orchestration id=%s for %s", instance_id, blob_name)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logging.warning("Orchestration start failed (attempt %d/%d): %s", 
                              attempt + 1, max_retries, e)
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    except Exception as e:
        logging.error("Processing failed for %s: %s", blob_name, e, exc_info=True)
        # Don't delete file on processing errors - will retry next cycle

