# Level 5 — Agent-to-Agent Communication: Multi-Agent Orchestration

Goal: Implement multi-agent workflows with inter-agent communication, tool coordination, and guardrails.

## Tasks
- Create blueprint `bp_multi_agent` with:
  - **Agent Orchestrator**: A durable orchestrator that coordinates multiple AI agents
  - **Agent Communication Hub**: Central message routing between agents with protocol validation
  - **Tool Registry**: Shared tool pool that agents can request access to based on capabilities
  - **Guardrail Engine**: Content filtering, token limits, and safety checks
- Implement agent workflows:
  - **Code Review Agent**: Analyzes snippets for security, style, and best practices
  - **Documentation Agent**: Generates comprehensive docs based on code review findings
  - **Testing Agent**: Suggests unit tests based on code analysis
- Add inter-agent protocols:
  - Message passing with structured schemas
  - Tool handoff mechanisms
  - Context sharing and state management
  - Conflict resolution for competing agent requests

## Acceptance
- Multiple agents can communicate through structured message protocols
- Orchestrator manages agent lifecycle and task distribution
- Guardrails prevent infinite loops, token exhaustion, and inappropriate content
- Agents can share tools and context while maintaining isolation
- All agent interactions are logged with correlation IDs

## Testing
- `tests/test_multi_agent_orchestration.py` with agent mocking
- Test agent communication protocols and error handling
- Validate guardrail enforcement and resource limits

## Env vars
- `MAX_AGENT_ITERATIONS`, `AGENT_TOKEN_LIMIT`, `ENABLE_CONTENT_FILTER`
- `AGENT_COMMUNICATION_TIMEOUT`, `MAX_CONCURRENT_AGENTS`

## Quickstart (local)
```bash
# Start multi-agent code review workflow
POST http://localhost:7071/api/orchestrators/multi-agent-review
{
  "projectId": "default-project",
  "snippetId": "example.py",
  "workflow": "code-review-and-docs"
}
```

## Architecture Patterns
- **Agent Registry**: Central catalog of available agents and their capabilities
- **Message Bus**: Structured communication with schema validation
- **Resource Pool**: Shared tools with access control and usage tracking
- **Circuit Breaker**: Prevents cascading failures in agent communication
- **State Machine**: Manages workflow progression and agent handoffs

## Guardrails Implementation
- Content filtering using Azure Content Safety
- Token counting and budget enforcement
- Timeout handling for stuck agents
- Rate limiting per agent type
- Audit logging for all inter-agent communications