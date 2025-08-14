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

import azure.functions as func
import azure.durable_functions as df

from data import cosmos_ops

bp = func.Blueprint()

CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "800"))


@bp.orchestration_trigger(context_name="context")
def embeddings_orchestrator(context: df.DurableOrchestrationContext) -> Generator[Any, Any, dict]:
    """Fan-out/fan-in to embed chunks and persist a snippet."""
    payload = context.get_input() or {}
    project_id: str = payload.get("projectId", "default-project")
    name: str = payload.get("name", "unnamed")
    text: str = payload.get("text", "")

    logging.info(f"ORCH start name={name} project={project_id} length={len(text)}")

    # Chunk deterministically
    chunks = [text[i : i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)] or [""]

    # Fan-out embedding calls
    tasks = [
        context.call_activity("embed_chunk_activity", {"chunkIndex": i, "text": ch})
        for i, ch in enumerate(chunks)
    ]
    embeddings: list[list[float]] = yield context.task_all(tasks)

    # Aggregate embeddings (simple mean vector)
    agg: list[float] = []
    if embeddings and embeddings[0]:
        dim = len(embeddings[0])
        sums = [0.0] * dim
        for vec in embeddings:
            for j in range(dim):
                sums[j] += float(vec[j])
        agg = [s / len(embeddings) for s in sums]

    # Persist via activity (keeps I/O out of orchestrator)
    result: dict = yield context.call_activity(
        "persist_snippet_activity",
        {"projectId": project_id, "name": name, "code": text, "embedding": agg},
    )

    logging.info("ORCH done name=%s chunks=%d", name, len(chunks))
    return result


@bp.activity_trigger(input_name="data")
async def embed_chunk_activity(data: str) -> list[float]:
    """Generate an embedding for a text chunk (async)."""
    from azure.identity.aio import DefaultAzureCredential
    from azure.ai.projects.aio import AIProjectClient
    # Prefer async inference client sourced from project

    # Handle both dict (from tests) and JSON string (from runtime)
    if isinstance(data, dict):
        data_dict = data
    else:
        try:
            data_dict = json.loads(data) if data else {}
        except json.JSONDecodeError:
            data_dict = {}
    
    text: str = data_dict.get("text", "")
    if not text:
        return []

    # Check for mock mode first, before checking required env vars
    if os.environ.get("DISABLE_OPENAI") == "1":
        # Return a tiny deterministic vector for tests/mock mode
        logging.info("Using mock embedding for text: %s", text[:50])
        return [0.0, 1.0, 0.0]

    # For real OpenAI mode, require environment variables
    model = os.environ.get("EMBEDDING_MODEL_DEPLOYMENT_NAME")
    conn = os.environ.get("PROJECT_CONNECTION_STRING")
    if not model or not conn:
        logging.warning("Missing OpenAI config, falling back to mock embedding")
        return [0.0, 1.0, 0.0]

    try:
        async with DefaultAzureCredential() as cred:
            async with AIProjectClient.from_connection_string(credential=cred, conn_str=conn) as proj:
                async with await proj.inference.get_embeddings_client() as embeds:
                    rsp = await embeds.embed(model=model, input=[text])
                    if not rsp.data or not rsp.data[0].embedding:
                        return []
                    return [float(x) for x in rsp.data[0].embedding]
    except Exception as e:
        logging.error("Embedding failed: %s", e, exc_info=True)
        return []


@bp.activity_trigger(input_name="data")
async def persist_snippet_activity(data: str) -> dict:
    """Persist snippet + embedding to Cosmos (async)."""
    # Handle both dict (from tests) and JSON string (from runtime)
    if isinstance(data, dict):
        data_dict = data
    else:
        try:
            data_dict = json.loads(data) if data else {}
        except json.JSONDecodeError:
            data_dict = {}
    
    name: str = data_dict.get("name", "unnamed")
    project_id: str = data_dict.get("projectId", "default-project")
    code: str = data_dict.get("code", "")
    embedding: list[float] = data_dict.get("embedding", [])

    try:
        result = await cosmos_ops.upsert_document(
            name=name, project_id=project_id, code=code, embedding=embedding
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
        function_name = "embeddings_orchestrator"
        # Start orchestration (async)
        instance_id = await client.start_new(orchestration_function_name=function_name, instance_id=None, client_input=body)
        logging.info("Started orchestration with ID = %s", instance_id)
        # Important: do not await this sync method
        return client.create_check_status_response(req, instance_id)
    except Exception as e:
        logging.error("HTTP starter error: %s", e, exc_info=True)
        return func.HttpResponse(body=json.dumps({"error": str(e)}), mimetype="application/json", status_code=500)
