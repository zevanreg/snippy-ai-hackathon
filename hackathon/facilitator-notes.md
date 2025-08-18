# Facilitator Notes

Common pitfalls and tips:
- Don’t await sync APIs (e.g., `req.get_json()`).
- Orchestrators must be `def` and use `yield` + `context.task_all`.
- Keep all I/O in activities; orchestrators orchestrate only.
- Ensure blueprints are registered exactly once.
- Log at INFO; include IDs and chunk counts.
- Use env vars that match `src/local.settings.example.json`.
- Deploy to Azure using `azd up` for testing and development.

Timeboxes:
- L1: 60–90 min, L2: 90–120 min, L3: 120 min, L4: 90 min.
- L5: 120–150 min (multi-agent orchestration), L6: 90–120 min (zero trust network).

Review checklist:
- Secrets not in code; only via `os.environ[...]`.
- Durable patterns correct; activities async.
- Tests exist and mock SDKs with AsyncMock/MagicMock.
- Vector search queries use top-K from env.
- L5: Agent communication uses structured schemas; guardrails prevent infinite loops.
- L6: All services use private endpoints; no public internet access; Managed Identity only.

Advanced Level Tips:
- L5: Test agent workflows with mocked OpenAI responses; validate message protocols.
- L6: Use Bicep templates for infrastructure; test network isolation with private endpoints.

Stretch ideas:
- Add role-based projects.
- Add simple UI page.
- Add retry policies and DLQ for failed blobs.
- L5+: Implement custom agent personalities and specialized workflows.
- L6+: Add compliance scanning and automated security alerts.
