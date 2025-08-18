# Instructions

## Core Platform (Levels 1-4)

Pre-requisites:

- Container name in env `INGESTION_CONTAINER` (default `snippet-input`).
- devcontainer includes PowerShell - use `pwsh` in terminal to use PS instead of linux shell

Steps (Windows PowerShell + Azure CLI):

### start function host

1) copy `local.settings.example.json`to `local.settings.json`, open the file and set the values. The contains values that can be used for local development. If you prefer to use azure resources replace the values with one from your environment.

1) Open a terminal, load the python environment and start the functions host

   ```bash
   cd src
   source .venv/bin/activate
   func host start
   ```

   The output should show that the function host started and there should be multiple functions running. **Leave this terminal open**.

1) Open a second terminal so we can test whether the functions are working. Run the following command:

   ```bash
   # Deploy to Azure first
   azd up
   
   # Test the health endpoint
   curl https://your-function-app.azurewebsites.net/api/health
   ```

   You should see a JSON-object containing the status "ok" - this means your functions are up and running!

   ```bash
   $ curl https://your-function-app.azurewebsites.net/api/health
   {"status": "ok", "timestamp": "2025-08-14T12:30:21.844151"}
   ```

### check storage (azure)

1) Store connectionstring in variable for later reference (below is the connection string for Azure Storage)

   ```powershell
   # PowerShell
   $STORAGE_CON_STR = "DefaultEndpointsProtocol=https;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
   ```

   ```bash
   STORAGE_CON_STR="DefaultEndpointsProtocol=https;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
   ```

1) Ensure container exists

   ```powershell
   az storage container create --name snippet-input --connection-string $STORAGE_CON_STR
   ```

   The output should either be `"created": true` if the container did not exist or `"created": false` if the container already existed.

1) Create a small test file and upload it

    ```powershell
    Set-Content -Path .\sample.md -Value "# Hello`nThis is a tiny doc to ingest."
    az storage blob upload --file .\sample.md --container-name snippet-input --name sample.md --connection-string $STORAGE_CON_STR --overwrite
    ```

    ```bash
    echo -e "# Hello\nThis is a tiny doc to ingest." > sample.md
    az storage blob upload --file sample.md --container-name snippet-input --name sample.md --connection-string "$STORAGE_CON_STR" --overwrite
    ```

### ensure durable function is working

1) Observe function logs

- The trigger should log: "Ingestion started orchestration id=... for sample.md".
- The Durable orchestration should fan-out embeddings and persist to Cosmos.

1) Verify durable instance (optional)

- Check the Functions console output for instanceId lines.
- For HTTP-driven orchestrations you’d poll the status URL; for blob-driven, use logs/App Insights.

Tip: To run without external AI calls, set `DISABLE_OPENAI=1` in `src/local.settings.json`.
