"""Embeddings orchestration blueprint.

- Orchestrator: sync def using yield + context.task_all
- Activities: async def and JSON-serialisable
- HTTP starter returns durable check status response
"""
from __future__ import annotations

import json
import logging
import os
from typing import Generator, Any
from urllib.parse import urlparse

import azure.functions as func
import azure.durable_functions as df

from data import cosmos_ops

bp = func.Blueprint()

CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "800"))


@bp.orchestration_trigger(context_name="context")
def embeddings_orchestrator(context: df.DurableOrchestrationContext) -> Generator[Any, Any, dict]:
    """Fan-out/fan-in to embed chunks and persist a snippet."""
    payload = context.get_input() or {}
    if not validate_input(payload):
        raise ValueError("Invalid input payload")

    project_id: str = payload.get("projectId", os.environ.get("DEFAULT_PROJECT_ID", "default-project"))
    snippets = payload.get("snippets", [])

    # Replay-aware logging for Durable orchestrations
    instance_id = getattr(context, "instance_id", "unknown")
    if context.is_replaying:
        logging.info("[REPLAY] ORCH replay instance=%s project=%s snippets=%d", instance_id, project_id, len(snippets))
    else:
        logging.info("[EXEC] ORCH start instance=%s project=%s snippets=%d", instance_id, project_id, len(snippets))
    chunkcount = 0
    result: dict = {}

    for snippet in snippets:
        name: str = snippet.get("name", "unnamed")
        text: str = snippet.get("code", "")
        language: str = snippet.get("language", "unknown")
        description: str = snippet.get("description", "no description")

        if not text:
            logging.warning("Skipping empty snippet %s", name)
            continue

        # Suppress noisy duplicate logs during replay
        if not context.is_replaying:
            logging.info("Processing snippet: %s", name)
        # 1. Chunk deterministically
        chunks = [text[i : i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)] or [""]
        chunkcount += len(chunks)

        # 2. Fan-out embedding calls
        tasks = [
            context.call_activity("embed_chunk_activity", {"chunkIndex": i, "text": ch})
            for i, ch in enumerate(chunks)
        ]

        # 3. Fan in: Wait for all results
        embeddings: list[list[float]] = yield context.task_all(tasks)
        
        # calculate an averaged embedding for this snipped (simple mean vector)
        agg: list[float] = []
        if embeddings and embeddings[0]:
            dim = len(embeddings[0])
            sums = [0.0] * dim
            for vec in embeddings:
                for j in range(dim):
                    sums[j] += float(vec[j])
            agg = [s / len(embeddings) for s in sums]

        # Persist via activity (keeps I/O out of orchestrator)
        result = yield context.call_activity(
            "persist_snippet_activity",
            {"projectId": project_id, "name": name, "code": text, "embedding": agg, "language": language, "description": description},
        )

    if context.is_replaying:
        logging.info("[REPLAY] ORCH done instance=%s chunks=%d", instance_id, chunkcount)
    else:
        logging.info("[EXEC] ORCH done instance=%s total_snippets=%d chunks=%d", instance_id, len(snippets), chunkcount)
    return result


@bp.activity_trigger(input_name="chunk")
async def embed_chunk_activity(chunk : dict) -> list[float]:
    """Generate an embedding for a text chunk (async)."""
    from azure.identity.aio import DefaultAzureCredential
    from azure.ai.projects.aio import AIProjectClient
    from azure.ai.inference.aio import EmbeddingsClient

    # Prefer async inference client sourced from project
    logging.info("Embedding chunk with async AIProjectClient")

    # Handle both dict (from tests) and JSON string (from runtime)
    if not isinstance(chunk, dict):
        try:
            chunk = json.loads(chunk) if chunk else {}
        except (json.JSONDecodeError, TypeError):
            chunk = {}

    text: str = chunk.get("text", "")
    if not text:
        return []

    # For real OpenAI mode, require environment variables
    model_name = os.environ.get("EMBEDDING_MODEL_DEPLOYMENT_NAME")
    conn = os.environ.get("PROJECT_CONNECTION_STRING")
    if not model_name or not conn:
        logging.warning("Missing OpenAI config, falling back to mock embedding")
        return [0.0, 1.0, 0.0]

    try:
        endpoint = f"https://{urlparse(conn).netloc}/models"

        async with EmbeddingsClient(
            endpoint=endpoint,
            credential=DefaultAzureCredential(),
            credential_scopes=["https://ai.azure.com/.default"],
        ) as embeddings_client:
            response = await embeddings_client.embed(
                model=model_name,
                input=[text]
            )
            
            # Ensure the embedding was generated successfully
            if not response.data or not response.data[0].embedding:
                logging.error("Failed to generate embedding. Response data: %s", response)
                raise ValueError("Failed to generate embedding.")
            
            query_vector = [float(x) for x in response.data[0].embedding]
            return query_vector
    except Exception as e:
        logging.error("Embedding failed: %s", e, exc_info=True)
        return []


@bp.activity_trigger(input_name="snippet")
async def persist_snippet_activity(snippet: dict) -> dict:
    """Persist snippet + embedding to Cosmos (async)."""
    # Handle both dict (from tests) and JSON string (from runtime)
    if not isinstance(snippet, dict):
        try:
            snippet = json.loads(snippet) if snippet else {}
        except (json.JSONDecodeError, TypeError):
            snippet = {}
    
    name: str = snippet.get("name", "unnamed")
    project_id: str = snippet.get("projectId", "default-project")
    code: str = snippet.get("code", "")
    embedding: list[float] = snippet.get("embedding", [])
    language: str = snippet.get("language", "unknown")
    description: str = snippet.get("description", "no description")

    try:
        result = await cosmos_ops.upsert_document(
            name=name, project_id=project_id, code=code, embedding=embedding, language=language, description=description
        )
        return {"ok": True, "id": result.get("id", name)}
    except Exception as e:
        logging.error("Persist failed: %s", e, exc_info=True)
        return {"ok": False, "error": str(e)}


@bp.route(route="orchestrators/embeddings", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
@bp.durable_client_input(client_name="client")
async def http_start_embeddings(req: func.HttpRequest, client: df.DurableOrchestrationClient) -> func.HttpResponse:
    """HTTP starter for embeddings orchestrator."""
    try:
        body = req.get_json()
        if not validate_input(body):
            return func.HttpResponse(body=json.dumps({"error": "Invalid input"}), mimetype="application/json", status_code=400)

        function_name = "embeddings_orchestrator"
        # Start orchestration (async)
        instance_id = await client.start_new(orchestration_function_name=function_name, instance_id=None, client_input=body)
        logging.info("Started orchestration with ID = %s", instance_id)
        # Important: do not await this sync method
        return client.create_check_status_response(req, instance_id)
    except Exception as e:
        logging.error("HTTP starter error: %s", e, exc_info=True)
        return func.HttpResponse(body=json.dumps({"error": str(e)}), mimetype="application/json", status_code=500)

def validate_input(input: dict) -> bool:
    """Validate the input JSON for the orchestration."""
    try:
        logging.info("Validating input: %s", input)
        if not isinstance(input, dict):
            return False
        # Required top-level fields
        
        if "snippets" not in input:
            return False
        snippets = input.get("snippets")
        # snippets must be a non-empty list (can relax to allow empty if desired)
        if not isinstance(snippets, list) or len(snippets) == 0:
            return False
        # Each snippet must be dict with name + code (non-empty code)
        for snip in snippets:
            if not isinstance(snip, dict):
                return False
            if "name" not in snip or "code" not in snip:
                return False
            if not isinstance(snip["code"], str) or snip["code"].strip() == "":
                return False
        return True
    except json.JSONDecodeError:
        return False