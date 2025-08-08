"""Blob-trigger ingestion blueprint.

- On blob upload, read text and kick off embeddings orchestrator
- Adds room for telemetry and retries
"""
from __future__ import annotations

import logging
import os

import azure.functions as func
import azure.durable_functions as df

bp = func.Blueprint()

INGESTION_CONTAINER = os.environ.get("INGESTION_CONTAINER", "snippet-input")
MAX_BLOB_MB = int(os.environ.get("MAX_BLOB_MB", "2"))


@bp.blob_trigger(
    arg_name="blob",
    path=f"{INGESTION_CONTAINER}/{{name}}",
    connection="AzureWebJobsStorage",
)
@bp.durable_client_input(client_name="client")
async def ingest_blob(blob: func.InputStream, name: str, client: df.DurableOrchestrationClient):
    """Trigger orchestration for uploaded text/markdown file."""
    try:
        size_mb = blob.length / (1024 * 1024)
        if size_mb > MAX_BLOB_MB:
            logging.warning("Skipping blob %s: size %.2fMB > limit %dMB", name, size_mb, MAX_BLOB_MB)
            return

        content_type = getattr(blob, "content_type", "text/plain") or "text/plain"
        if not (content_type.startswith("text/") or name.lower().endswith((".md", ".txt"))):
            logging.info("Skipping non-text blob: %s (%s)", name, content_type)
            return

        text = blob.read().decode("utf-8", errors="ignore")
        payload = {"projectId": os.environ.get("DEFAULT_PROJECT_ID", "default-project"), "name": name, "text": text}

        try:
            instance_id = await client.start_new("embeddings_orchestrator", None, payload)
        except TypeError:
            instance_id = client.start_new("embeddings_orchestrator", None, payload)

        logging.info("Ingestion started orchestration id=%s for %s", instance_id, name)
    except Exception as e:
        logging.error("Ingestion failed: %s", e, exc_info=True)
        # In production, consider DLQ or retry policies
