# Facilitator Notes

Common pitfalls and tips:
- Don’t await sync APIs (e.g., `req.get_json()`).
- Orchestrators must be `def` and use `yield` + `context.task_all`.
- Keep all I/O in activities; orchestrators orchestrate only.
- Ensure blueprints are registered exactly once.
- Log at INFO; include IDs and chunk counts.
- Use env vars that match `src/local.settings.example.json`.
- For local dev, use `UseDevelopmentStorage=true` for storage.

Timeboxes:
- L1: 60–90 min, L2: 90–120 min, L3: 120 min, L4: 90 min.

Review checklist:
- Secrets not in code; only via `os.environ[...]`.
- Durable patterns correct; activities async.
- Tests exist and mock SDKs with AsyncMock/MagicMock.
- Vector search queries use top-K from env.

Stretch ideas:
- Add role-based projects.
- Add simple UI page.
- Add retry policies and DLQ for failed blobs.
