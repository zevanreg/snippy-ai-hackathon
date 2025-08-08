# Level 1 — Foundation API + Persistence

Goal: Basic HTTP API for CRUD snippets + health check.

## Tasks
- Add HTTP routes:
  - `GET /health` => 200 {"status":"ok"}
  - `POST /snippets` (already exists) — ensure proper validation and logging
  - `GET /snippets/{name}` (already exists)
  - `GET /snippets?tag=` (optional stretch)
- Use Cosmos helpers in `data/cosmos_ops.py` for persistence.
- Use env vars from `src/local.settings.json`.
- Use logging (INFO); no prints. Type hints everywhere.

## Acceptance
- Endpoints return correct status codes and JSON.
- No sync APIs are awaited; secrets via env only.
- Tests pass locally.

## Hints
- Follow blueprint model: global `app = func.FunctionApp()` once.
- Reuse existing snippet save/get endpoints.
- Keep payloads small in tests; patch Cosmos with MagicMock.

## Testing
- Create `tests/test_level1_endpoints.py` with positive/negative paths.
- Use `pytest`.

## Run
- Start: VS Code task "func: host start"
- Test: `python -m pytest -q`

---

## Quickstart (local)
Windows PowerShell examples for local testing. Ensure `src/local.settings.json` is configured and the Functions host is running.

- Save a snippet

```powershell
$body = @{ name = "hello"; code = "print('hi')" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:7071/api/snippets -ContentType application/json -Body $body
```

- Get a snippet

```powershell
Invoke-RestMethod -Uri http://localhost:7071/api/snippets/hello
```

- Health (if you implemented `/health`)

```powershell
Invoke-RestMethod -Uri http://localhost:7071/api/health
```

Tip: You can also use the REST collection at `src/tests/test.http` in VS Code.
