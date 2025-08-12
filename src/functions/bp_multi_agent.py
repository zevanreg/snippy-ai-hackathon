"""Multi-agent orchestration blueprint (Level 5).

- Orchestrator: sync def using yield + context.task_all
- Activities: async def and JSON-serialisable
- Pattern: Load -> Review -> (Docs, Tests)
- Guardrails: max iterations, token budget, basic content filter
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Generator

import azure.functions as func
import azure.durable_functions as df

from data import cosmos_ops

bp = func.Blueprint()


# ---------------------------
# Config (env-driven)
# ---------------------------
MAX_AGENT_ITERATIONS = int(os.environ.get("MAX_AGENT_ITERATIONS", "3"))
AGENT_TOKEN_LIMIT = int(os.environ.get("AGENT_TOKEN_LIMIT", "4000"))
ENABLE_CONTENT_FILTER = os.environ.get("ENABLE_CONTENT_FILTER", "0") == "1"
MAX_CONCURRENT_AGENTS = int(os.environ.get("MAX_CONCURRENT_AGENTS", "3"))


def _apply_guardrails(code: str, *, token_limit: int = AGENT_TOKEN_LIMIT, enable_filter: bool = ENABLE_CONTENT_FILTER) -> tuple[str, list[str]]:
    """Apply simple guardrails: truncate to token budget and basic content screen."""
    issues: list[str] = []

    # Approx token:chars 1:4 heuristic to keep deterministic in orch
    max_chars = max(256, token_limit * 4)
    if len(code) > max_chars:
        issues.append(f"truncated:{len(code)}->{max_chars}")
        code = code[:max_chars]

    if enable_filter:
        banned = ["DROP TABLE", "rm -rf", "BEGIN RSA PRIVATE KEY", "AKIA"]
        found = [w for w in banned if w.lower() in code.lower()]
        if found:
            issues.append("content-filter:blocked")
            # Redact risky fragments
            for w in found:
                code = code.replace(w, "[REDACTED]")

    return code, issues


@bp.orchestration_trigger(context_name="context")
def multi_agent_orchestrator(context: df.DurableOrchestrationContext) -> Generator[Any, Any, dict]:
    """Coordinate agents to review a snippet, then write docs and tests."""
    payload: dict = context.get_input() or {}
    project_id: str = payload.get("projectId", "default-project")
    snippet_id: str = payload.get("snippetId", payload.get("name", ""))
    workflow: str = payload.get("workflow", "code-review-and-docs")

    corr = context.instance_id
    logging.info("L5 ORCH start id=%s project=%s snippet=%s wf=%s", corr, project_id, snippet_id, workflow)

    if not snippet_id:
        return {"ok": False, "error": "snippetId is required", "correlationId": corr}

    # Iteration budget check (single cycle uses 2 steps: review + docs/tests)
    if MAX_AGENT_ITERATIONS < 2:
        return {"ok": False, "error": "MAX_AGENT_ITERATIONS too low", "correlationId": corr}

    # Phase 0: Load snippet (I/O in activity)
    snippet: dict = yield context.call_activity("load_snippet_activity", {"name": snippet_id})
    code_text: str = (snippet or {}).get("code", "")

    # Guardrails in orchestrator are deterministic
    safe_code, guardrail_issues = _apply_guardrails(code_text)

    # Phase 1: Code review (sequential)
    review: dict = yield context.call_activity(
        "code_review_agent_activity",
        {"code": safe_code, "projectId": project_id, "correlationId": corr},
    )

    # Phase 2: Fan-out docs + tests (dependent on review)
    tasks = [
        context.call_activity(
            "documentation_agent_activity",
            {"code": safe_code, "review": review, "projectId": project_id, "correlationId": corr},
        ),
        context.call_activity(
            "testing_agent_activity",
            {"code": safe_code, "review": review, "projectId": project_id, "correlationId": corr},
        ),
    ]
    docs_result, tests_result = yield context.task_all(tasks)

    result: dict = {
        "ok": True,
        "correlationId": corr,
        "guardrails": guardrail_issues,
        "agents": {
            "review": review,
            "documentation": docs_result,
            "testing": tests_result,
        },
    }

    logging.info("L5 ORCH done id=%s", corr)
    return result


@bp.activity_trigger(input_name="data")
async def load_snippet_activity(data: dict) -> dict:
    """Load a snippet by id from Cosmos (async)."""
    name: str = (data or {}).get("name", "")
    if not name:
        return {}
    try:
        doc = await cosmos_ops.get_snippet_by_id(name)
        return doc or {}
    except Exception as e:
        logging.error("load_snippet failed: %s", e, exc_info=True)
        return {}


@bp.activity_trigger(input_name="data")
async def code_review_agent_activity(data: dict) -> dict:
    """Analyze code for issues; return structured findings (async)."""
    code: str = (data or {}).get("code", "")
    corr: str = (data or {}).get("correlationId", "")
    if os.environ.get("DISABLE_OPENAI") == "1":
        # Deterministic mock results
        issues = []
        if "print(" in code:
            issues.append({"type": "style", "message": "Avoid prints; use logging.", "severity": "low"})
        if len(code) > 2000:
            issues.append({"type": "perf", "message": "Large function body; consider refactor.", "severity": "medium"})
        return {"summary": "Mock review", "issues": issues, "correlationId": corr}

    # Real model call omitted for brevity; rely on mock in tests
    return {"summary": "Review executed", "issues": [], "correlationId": corr}


@bp.activity_trigger(input_name="data")
async def documentation_agent_activity(data: dict) -> dict:
    """Generate docs from code and review findings (async)."""
    code: str = (data or {}).get("code", "")
    review: dict = (data or {}).get("review", {})
    corr: str = (data or {}).get("correlationId", "")

    title = "Code Documentation"
    bullets = [f"Issues found: {len(review.get('issues', []))}"]
    if any(i.get("type") == "style" for i in review.get("issues", [])):
        bullets.append("Adopt logging best practices; avoid prints.")
    content = "\n".join([f"# {title}", "", *("- " + b for b in bullets)])

    return {"markdown": content, "size": len(code), "correlationId": corr}


@bp.activity_trigger(input_name="data")
async def testing_agent_activity(data: dict) -> dict:
    """Suggest simple unit tests based on code and review (async)."""
    code: str = (data or {}).get("code", "")
    review: dict = (data or {}).get("review", {})
    corr: str = (data or {}).get("correlationId", "")

    tests: list[dict[str, Any]] = []
    if "def " in code:
        tests.append({"name": "test_function_exists", "assert": "callable"})
    if any(i.get("severity") == "medium" for i in review.get("issues", [])):
        tests.append({"name": "test_performance_boundaries", "assert": "runtime<1s"})

    return {"tests": tests, "count": len(tests), "correlationId": corr}


@bp.route(route="orchestrators/multi-agent-review", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
@bp.durable_client_input(client_name="client")
async def http_start_multi_agent(req: func.HttpRequest, client: df.DurableOrchestrationClient) -> func.HttpResponse:
    """HTTP starter for multi-agent orchestrator."""
    try:
        body = req.get_json()
        fn = "multi_agent_orchestrator"
        try:
            instance_id = await client.start_new(function_name=fn, instance_id=None, client_input=body)
        except TypeError:
            instance_id = client.start_new(function_name=fn, instance_id=None, client_input=body)
        logging.info("Started L5 orchestration id=%s", instance_id)
        return client.create_check_status_response(req, instance_id)
    except Exception as e:
        logging.error("HTTP starter L5 error: %s", e, exc_info=True)
        return func.HttpResponse(body=json.dumps({"error": str(e)}), mimetype="application/json", status_code=500)
