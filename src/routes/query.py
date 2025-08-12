"""Query endpoint composing grounded answers with citations."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import azure.functions as func
from agents.tools import vector_search as vs

bp = func.Blueprint()

TOP_K = int(os.environ.get("VECTOR_TOP_K", os.environ.get("COSMOS_VECTOR_TOP_K", "5")))
TEMP = float(os.environ.get("OPENAI_TEMPERATURE", "0.2"))
REQ_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT_SEC", "20"))


@bp.route(route="security/rbac-check", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
async def http_rbac_check(req: func.HttpRequest) -> func.HttpResponse:
    """Verify app can read Cosmos container using Managed Identity."""
    try:
        # Try a small metadata call to ensure RBAC is valid
        from data import cosmos_ops
        container = await cosmos_ops.get_container()
        # Listing properties is enough to assert access
        name = getattr(container, 'container_link', None) or 'ok'
        return func.HttpResponse(
            body=json.dumps({"ok": True, "container": str(name)}),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        logging.error("RBAC check failed: %s", e, exc_info=True)
        return func.HttpResponse(
            body=json.dumps({"ok": False, "error": str(e)}),
            mimetype="application/json",
            status_code=403,
        )


@bp.route(route="query", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
async def http_query(req: func.HttpRequest) -> func.HttpResponse:
    """Answer a question using vector search and LLM, returning citations."""
    try:
        body = req.get_json()
        question: str = body.get("question", "").strip()
        project_id: str = body.get("projectId", "default-project")
        if not question:
            return func.HttpResponse(
                body=json.dumps({"error": "question is required"}),
                mimetype="application/json",
                status_code=400,
            )

        # Vector search for grounding docs
        raw = await vs.vector_search(query=question, k=TOP_K, project_id=project_id)
        results = json.loads(raw)
        if isinstance(results, dict) and results.get("error"):
            return func.HttpResponse(body=raw, mimetype="application/json", status_code=502)

        contexts = [r.get("code", "") for r in results]
        citations = [{"id": r.get("id"), "score": r.get("score")} for r in results]

        # Compose prompt
        system = "You are a concise assistant. Answer using provided snippets. Cite ids."
        prompt = f"Question: {question}\n\nSnippets:\n" + "\n---\n".join(contexts)

        # Call chat model (async), prefer Azure AI Projects if available
        answer, usage = await _chat_complete(system, prompt)

        payload: dict[str, Any] = {"answer": answer, "citations": citations, "usage": usage}
        return func.HttpResponse(body=json.dumps(payload), mimetype="application/json", status_code=200)
    except Exception as e:
        logging.error("Query failed: %s", e, exc_info=True)
        return func.HttpResponse(body=json.dumps({"error": str(e)}), mimetype="application/json", status_code=500)


async def _chat_complete(system: str, user: str) -> tuple[str, dict]:
    """Call Azure OpenAI Chat asynchronously; supports mock via env."""
    if os.environ.get("DISABLE_OPENAI") == "1":
        return ("This is a mocked answer.", {"mock": True})

    from azure.identity import DefaultAzureCredential
    from azure.ai.projects.aio import AIProjectClient

    model = os.environ.get("AGENTS_MODEL_DEPLOYMENT_NAME") or os.environ.get("OPENAI_CHAT_MODEL")
    conn = os.environ.get("PROJECT_CONNECTION_STRING")
    if not model or not conn:
        return ("Model or connection not configured.", {"error": True})

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    try:
        cred = DefaultAzureCredential()
        async with AIProjectClient.from_connection_string(credential=cred, conn_str=conn) as proj:
            async with await proj.inference.get_chat_completions_client() as chat:
                rsp = await chat.complete(model=model, messages=messages, temperature=TEMP)
                text = rsp.choices[0].message.content if rsp.choices else ""
                usage = getattr(rsp, "usage", {}) or {}
                return (text, dict(usage))
    except Exception as e:
        logging.error("Chat completion failed: %s", e, exc_info=True)
        return ("", {"error": str(e)})
