"""Multi-agent orchestration blueprint (Level 5).

- Orchestrator: sync def using yield + context.task_all
- Activities: async def and JSON-serialisable
- Pattern: Load -> Review -> (Docs, Tests)
- Guardrails: max iterations, token budget, basic content filter
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Generator

import azure.functions as func
import azure.durable_functions as df
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

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
    if not isinstance(data, dict):
        try:
            data = json.loads(data) if data else {}
        except (json.JSONDecodeError, TypeError):
            data = {}
    
    name: str = data.get("name", "")
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
    """Analyze code for issues using Azure AI agent; return structured findings (async)."""
    if not isinstance(data, dict):
        try:
            data = json.loads(data) if data else {}
        except (json.JSONDecodeError, TypeError):
            data = {}
    
    code: str = data.get("code", "")
    corr: str = data.get("correlationId", "")
    
    # Check for mock mode
    if os.environ.get("DISABLE_OPENAI") == "1":
        mock_issues = []
        # Mock style issue for print statements
        if "print(" in code:
            mock_issues.append({
                "type": "style",
                "message": "Consider using logging instead of print statements",
                "line": 1
            })
        return {"summary": "Review executed (mock)", "issues": mock_issues, "correlationId": corr}
    
    try:
        # System prompt for code review agent
        system_prompt = """
You are a CodeReviewAgent, an expert code analyzer that identifies issues and provides feedback.

Analyze the provided code for:
1. Security vulnerabilities (SQL injection, XSS, code injection, etc.)
2. Performance issues (inefficient algorithms, memory leaks, etc.)
3. Code quality problems (poor naming, missing documentation, etc.)
4. Best practices violations (error handling, logging, etc.)
5. Potential bugs and logic errors

Return your analysis as a JSON object with this structure:
{
    "summary": "Brief overview of the code review",
    "issues": [
        {
            "type": "security|performance|quality|bug|style",
            "severity": "high|medium|low",
            "line": line_number_if_applicable,
            "description": "Description of the issue",
            "recommendation": "How to fix the issue"
        }
    ],
    "overall_score": 1-10_rating,
    "recommendations": ["List of general recommendations"]
}

Be thorough but concise in your analysis.
"""
        
        project_client = AIProjectClient(
            endpoint=os.environ["PROJECT_CONNECTION_STRING"],
            credential=DefaultAzureCredential(),
        )
        
        async with project_client:
            # Create the code review agent
            agent = await project_client.agents.create_agent(
                name="CodeReviewAgent",
                description="Code analysis and review agent",
                instructions=system_prompt,
                model=os.environ["AGENTS_MODEL_DEPLOYMENT_NAME"]
            )
            
            # Create thread and add the code to review
            thread = await project_client.agents.threads.create()
            await project_client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Please analyze this code:\n\n```\n{code}\n```"
            )
            
            # Run the agent
            run = await project_client.agents.runs.create(
                thread_id=thread.id,
                agent_id=agent.id
            )
            
            # Wait for completion
            while True:
                run = await project_client.agents.runs.get(thread_id=thread.id, run_id=run.id)
                if run.status == "completed":
                    break
                elif run.status == "failed":
                    logging.error("Code review agent failed: %s", run)
                    return {"summary": "Review failed", "issues": [], "correlationId": corr}
                
                await asyncio.sleep(1)
            
            # Get the response
            messages_pager = project_client.agents.messages.list(
                thread_id=thread.id,
                order="desc",
                limit=1
            )
            
            messages = []
            async for message in messages_pager:
                messages.append(message)
                break  # Only get the first (latest) message
            
            if messages:
                response_content = messages[0].content[0].text.value
                try:
                    # Parse JSON response
                    review_result = json.loads(response_content)
                    review_result["correlationId"] = corr
                    return review_result
                except json.JSONDecodeError:
                    # Fallback if response isn't JSON
                    return {
                        "summary": response_content[:200],
                        "issues": [],
                        "correlationId": corr
                    }
            
            return {"summary": "No response", "issues": [], "correlationId": corr}
            
    except Exception as e:
        logging.error("Code review agent error: %s", e, exc_info=True)
        return {"summary": f"Error: {str(e)}", "issues": [], "correlationId": corr}


@bp.activity_trigger(input_name="data")
async def documentation_agent_activity(data: dict) -> dict:
    """Generate docs from code and review findings using Azure AI agent (async)."""
    if not isinstance(data, dict):
        try:
            data = json.loads(data) if data else {}
        except (json.JSONDecodeError, TypeError):
            data = {}
    
    code: str = data.get("code", "")
    review: dict = data.get("review", {})
    corr: str = data.get("correlationId", "")

    # Check for mock mode
    if os.environ.get("DISABLE_OPENAI") == "1":
        title = "Code Documentation"
        bullets = [f"Issues found: {len(review.get('issues', []))}"]
        if any(i.get("type") == "style" for i in review.get("issues", [])):
            bullets.append("Adopt logging best practices; avoid prints.")
        content = "\n".join([f"# {title}", "", *("- " + b for b in bullets)])
        return {"markdown": content, "size": len(code), "correlationId": corr}
    
    try:
        # System prompt for documentation agent
        system_prompt = """
You are a DocumentationAgent, an expert technical writer that creates comprehensive documentation for code.

Based on the provided code and code review findings, create comprehensive documentation in Markdown format that includes:

1. **Overview**: Brief description of what the code does
2. **Functions/Classes**: Document each function and class with:
   - Purpose and functionality
   - Parameters and return values
   - Usage examples
3. **Code Quality Notes**: Based on review findings, document:
   - Known issues and their impact
   - Recommended improvements
   - Best practices to follow
4. **Usage Examples**: Practical examples of how to use the code
5. **Notes**: Any additional important information

Focus on clarity and usefulness for developers who will use or maintain this code.
Return only the Markdown documentation, no additional commentary.
"""
        
        project_client = AIProjectClient(
            endpoint=os.environ["PROJECT_CONNECTION_STRING"],
            credential=DefaultAzureCredential(),
        )
        
        async with project_client:
            # Create the documentation agent
            agent = await project_client.agents.create_agent(
                name="DocumentationAgent",
                description="Technical documentation generation agent",
                instructions=system_prompt,
                model=os.environ["AGENTS_MODEL_DEPLOYMENT_NAME"]
            )
            
            # Create thread and add the code and review
            thread = await project_client.agents.threads.create()
            
            # Prepare context message
            context_message = f"""Please create documentation for this code:

```
{code}
```

Code Review Results:
- Issues found: {len(review.get('issues', []))}
- Summary: {review.get('summary', 'No summary available')}

Review Issues:
"""
            
            for issue in review.get('issues', []):
                context_message += f"- {issue.get('type', 'unknown')}: {issue.get('description', 'No description')}\n"
            
            await project_client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=context_message
            )
            
            # Run the agent
            run = await project_client.agents.runs.create(
                thread_id=thread.id,
                agent_id=agent.id
            )
            
            # Wait for completion
            while True:
                run = await project_client.agents.runs.get(thread_id=thread.id, run_id=run.id)
                if run.status == "completed":
                    break
                elif run.status == "failed":
                    logging.error("Documentation agent failed: %s", run)
                    return {"markdown": "Documentation generation failed", "size": len(code), "correlationId": corr}
                
                await asyncio.sleep(1)
            
            # Get the response
            messages_pager = project_client.agents.messages.list(
                thread_id=thread.id,
                order="desc",
                limit=1
            )
            
            messages = []
            async for message in messages_pager:
                messages.append(message)
                break
            
            if messages:
                markdown_content = messages[0].content[0].text.value
                return {"markdown": markdown_content, "size": len(code), "correlationId": corr}
            
            return {"markdown": "No documentation generated", "size": len(code), "correlationId": corr}
            
    except Exception as e:
        logging.error("Documentation agent error: %s", e, exc_info=True)
        return {"markdown": f"Error generating documentation: {str(e)}", "size": len(code), "correlationId": corr}


@bp.activity_trigger(input_name="data")
async def testing_agent_activity(data: dict) -> dict:
    """Generate unit tests based on code and review using Azure AI agent (async)."""
    if not isinstance(data, dict):
        try:
            data = json.loads(data) if data else {}
        except (json.JSONDecodeError, TypeError):
            data = {}
    
    code: str = data.get("code", "")
    review: dict = data.get("review", {})
    corr: str = data.get("correlationId", "")

    # Check for mock mode
    if os.environ.get("DISABLE_OPENAI") == "1":
        tests: list[dict[str, Any]] = []
        if "def " in code:
            tests.append({"name": "test_function_exists", "assert": "callable"})
        if any(i.get("severity") == "medium" for i in review.get("issues", [])):
            tests.append({"name": "test_performance_boundaries", "assert": "runtime<1s"})
        return {"tests": tests, "count": len(tests), "correlationId": corr}
    
    try:
        # System prompt for testing agent
        system_prompt = """
You are a TestingAgent, an expert at generating comprehensive unit tests for code.

Based on the provided code and code review findings, generate unit tests that cover:

1. **Basic Functionality**: Test that functions work as expected with valid inputs
2. **Edge Cases**: Test boundary conditions, empty inputs, None values, etc.
3. **Error Handling**: Test that appropriate exceptions are raised for invalid inputs
4. **Performance**: Based on review findings, add performance tests if needed
5. **Security**: Test for security issues identified in the review

Return your response as a JSON object with this structure:
{
    "tests": [
        {
            "name": "test_function_name",
            "description": "What this test validates",
            "code": "Python test code using pytest",
            "type": "unit|integration|performance|security"
        }
    ],
    "count": number_of_tests,
    "framework": "pytest",
    "setup_required": ["list of setup requirements if any"]
}

Focus on practical, executable tests that would catch real issues.
"""
        
        project_client = AIProjectClient(
            endpoint=os.environ["PROJECT_CONNECTION_STRING"],
            credential=DefaultAzureCredential(),
        )
        
        async with project_client:
            # Create the testing agent
            agent = await project_client.agents.create_agent(
                name="TestingAgent",
                description="Unit test generation agent",
                instructions=system_prompt,
                model=os.environ["AGENTS_MODEL_DEPLOYMENT_NAME"]
            )
            
            # Create thread and add the code and review
            thread = await project_client.agents.threads.create()
            
            # Prepare context message
            context_message = f"""Please generate unit tests for this code:

```
{code}
```

Code Review Results:
- Issues found: {len(review.get('issues', []))}
- Summary: {review.get('summary', 'No summary available')}

Specific Issues to Test:
"""
            
            for issue in review.get('issues', []):
                context_message += f"- {issue.get('type', 'unknown')} ({issue.get('severity', 'unknown')}): {issue.get('description', 'No description')}\n"
            
            context_message += "\nPlease generate comprehensive tests that cover the functionality and address the identified issues."
            
            await project_client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=context_message
            )
            
            # Run the agent
            run = await project_client.agents.runs.create(
                thread_id=thread.id,
                agent_id=agent.id
            )
            
            # Wait for completion
            while True:
                run = await project_client.agents.runs.get(thread_id=thread.id, run_id=run.id)
                if run.status == "completed":
                    break
                elif run.status == "failed":
                    logging.error("Testing agent failed: %s", run)
                    return {"tests": [], "count": 0, "correlationId": corr}
                
                await asyncio.sleep(1)
            
            # Get the response
            messages_pager = project_client.agents.messages.list(
                thread_id=thread.id,
                order="desc",
                limit=1
            )
            
            messages = []
            async for message in messages_pager:
                messages.append(message)
                break
            
            if messages:
                response_content = messages[0].content[0].text.value
                try:
                    # Parse JSON response
                    test_result = json.loads(response_content)
                    test_result["correlationId"] = corr
                    return test_result
                except json.JSONDecodeError:
                    # Fallback if response isn't JSON
                    return {
                        "tests": [{"name": "generated_test", "description": response_content[:200]}],
                        "count": 1,
                        "correlationId": corr
                    }
            
            return {"tests": [], "count": 0, "correlationId": corr}
            
    except Exception as e:
        logging.error("Testing agent error: %s", e, exc_info=True)
        return {"tests": [], "count": 0, "error": str(e), "correlationId": corr}


@bp.route(route="orchestrators/multi-agent-review", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
@bp.durable_client_input(client_name="client")
async def http_start_multi_agent(req: func.HttpRequest, client: df.DurableOrchestrationClient) -> func.HttpResponse:
    """HTTP starter for multi-agent orchestrator."""
    try:
        body = req.get_json()
        fn = "multi_agent_orchestrator"
        instance_id = await client.start_new(orchestration_function_name=fn, instance_id=None, client_input=body)
        logging.info("Started L5 orchestration id=%s", instance_id)
        return client.create_check_status_response(req, instance_id)
    except Exception as e:
        logging.error("HTTP starter L5 error: %s", e, exc_info=True)
        return func.HttpResponse(body=json.dumps({"error": str(e)}), mimetype="application/json", status_code=500)
