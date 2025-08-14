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

### Option 1: Local Development
- Start: VS Code task "func: host start"
- Test: `python -m pytest -q`

### Option 2: Cloud Deployment with AZD
```bash
# Deploy to Azure
azd auth login
azd up

# Test against cloud endpoint (replace with your function app URL)
curl https://your-function-app.azurewebsites.net/api/health
```

---

## Quickstart (local)
Windows PowerShell examples for local testing. Ensure `src/local.settings.json` is configured and the Functions host is running.

### Local Development Examples

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

### Cloud Deployment Examples
After deploying with `azd up`, test against your cloud endpoint:

```powershell
# Get your function app URL from azd output
$functionAppUrl = "https://your-function-app.azurewebsites.net"

# Save a snippet
$body = @{ name = "hello"; code = "print('hi')" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$functionAppUrl/api/snippets" -ContentType application/json -Body $body

# Get a snippet
Invoke-RestMethod -Uri "$functionAppUrl/api/snippets/hello"

# Health check
Invoke-RestMethod -Uri "$functionAppUrl/api/health"
```

Note: Replace `your-function-app.azurewebsites.net` with the actual URL from your `azd up` deployment output.
