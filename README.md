<!--
---
name: Snippy - Intelligent Code Snippet Service with MCP Tools
description: A serverless code snippet management service using Azure Functions, Durable Functions, Azure OpenAI, and Azure AI Agents.
page_type: sample
languages:
- python
- bicep
- azdeveloper
products:
- azure-functions
- azure-durable-functions
- azure-openai
- azure-cosmos-db
- azure-blob-storage
- azure-ai-agents
urlFragment: snippy
---
-->

<p align="center">
  <img src="https://raw.githubusercontent.com/Azure-Samples/snippy/main/.github/assets/snippy-logo.svg" alt="Snippy logo" width="220"><br>
  <b>Snippy · Intelligent Code-Snippet Service with MCP Tools</b>
</p>

🧩 **Snippy** is a serverless, AI-powered code snippet management service built on **Azure Functions (Python v2)**. It demonstrates how to:
* Use **Durable Functions** for complex workflows (e.g., fan-out/fan-in).
* Integrate with **Azure OpenAI** to generate vector embeddings.
* Store and query data, including vectors, in **Azure Cosmos DB**.
* Leverage **Azure AI Agents** service for advanced code analysis and generation tasks.
* Expose backend capabilities as **Model Context Protocol (MCP) tools** consumable by Agents (acting as MCP Hosts) like **GitHub Copilot Agent Mode** in VS Code.

> 💡 This project is inspired by the [Remote MCP Functions Python Sample](https://github.com/Azure-Samples/remote-mcp-functions-python), which demonstrates the core concepts of building MCP tools with Azure Functions.

---

## ✨ Feature Highlights

Snippy provides both standard HTTP endpoints and MCP Tools for interacting with code snippets:

| Feature | How it Works | Core Technologies | MCP Tool(s) |
|---|---|---|---|
| 📦 **Save Snippet** | HTTP/MCP trigger initiates a Durable Function orchestrator. | *Fan-out:* Uploads raw code to **Blob Storage** & generates embeddings via **Azure OpenAI**. <br> *Fan-in:* Upserts snippet metadata + vector embedding into **Cosmos DB**. | `save_snippet` |
| 🔍 **Get Snippet** | HTTP/MCP trigger directly fetches snippet data (including code, metadata) from **Cosmos DB**. | Azure Functions, Cosmos DB | `get_snippet` |
| 🔬 **Deep Research** | HTTP/MCP trigger fetches snippet & similar snippets (via vector search) from **Cosmos DB**, then uses **Azure AI Agents** service to generate a detailed analysis. | Azure Functions, Cosmos DB (Vector Search), Azure AI Agents | `deep_research` |
| 🎨 **Style Guide Generation** | HTTP/MCP trigger fetches snippet & similar snippets from **Cosmos DB**, then uses **Azure AI Agents** service to generate a language-specific code style guide. | Azure Functions, Cosmos DB (Vector Search), Azure AI Agents | `code_style` |
| 🧠 **Semantic Search** | **Cosmos DB's integrated vector database** capabilities enable finding snippets based on semantic similarity (used by Research & Style Guide features). | Cosmos DB | *(Internal)* |
| 🔄 **Durable Workflows** | Complex operations like saving snippets leverage **Durable Functions** orchestrators for reliable, parallel execution of activities. | Azure Durable Functions | *(Internal)* |
| 🛠 **Remote MCP Server** | Azure Functions hosts the `mcpToolTrigger` and the required SSE endpoint (`/runtime/webhooks/mcp/sse`), making tools discoverable and invokable by MCP clients like **GitHub Copilot Chat**. | Azure Functions (MCP Trigger) | *(All)* |

---

## 🌐 Why MCP?

[Model Context Protocol (MCP)](https://aka.ms/mcp) allows applications to advertise and execute custom tools for Large Language Models (LLMs). The **remote MCP trigger** in Azure Functions (see the [announcement blog](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/build-ai-agent-tools-using-remote-mcp-with-azure-functions/ba-p/4113709)) provides significant advantages:

* **Simplified Infrastructure:** No need for a separate MCP server; `func start` includes it.
* **Scalability:** Leverage Azure Functions scaling (including Flex Consumption) when Copilot calls your tools.
* **Real-time Updates:** Server-Sent Events (SSE) streaming allows Copilot to display live progress from Functions.
* **Built-in Security:** Utilize standard Azure Functions authentication (keys, identity).

Snippy uses these MCP triggers to surface its snippet management and analysis capabilities directly within **GitHub Copilot Chat** and other compatible clients.

---

## 🏗️ Architecture

```mermaid
graph LR
  subgraph "Clients"
    Copilot[GitHub Copilot Chat /<br>MCP Client]
    User[User via HTTP]
  end

  subgraph "Azure Functions App (Snippy)"
    direction TB
    subgraph "Triggers"
      direction LR
      MCPTools["MCP Tools<br>(mcpToolTrigger)"]:::tool
      HttpApi["HTTP API<br>(httpTrigger)"]:::tool
    end

    subgraph "Orchestration & Activities"
      direction TB
      Orch[("save_snippet_orchestrator<br>(Durable Function)")]
      subgraph "Activities"
        direction LR
        BlobAct("Blob Upload")
        EmbedAct("Generate Embedding")
        CosmosAct("Cosmos Upsert/Query")
        AgentAct("Invoke AI Agent")
      end
    end

    MCPTools -- "save_snippet" --> Orch
    HttpApi -- "POST /snippets" --> Orch

    Orch -- Fan-out --> BlobAct
    Orch -- Fan-out --> EmbedAct
    BlobAct -- Blob URL --> Orch
    EmbedAct -- Embedding --> Orch
    Orch -- Fan-in & Upsert Call --> CosmosAct

    MCPTools -- "get/research/style" --> CosmosAct
    HttpApi -- "GET/POST ..." --> CosmosAct
    MCPTools -- "research/style" --> AgentAct
    HttpApi -- "POST .../research|style" --> AgentAct
    AgentAct -- Uses Data From --> CosmosAct

  end

  subgraph "Azure Services"
    Blob[(Azure Blob Storage)]
    Cosmos[(Azure Cosmos DB<br>+ Vector Index)]
    AOAI(Azure OpenAI<br>Embedding Model)
    AIAgents(Azure AI Agents Service<br>via AI Project)
  end

  classDef tool fill:#4F46E5,color:#fff,stroke:#4F46E5

  Copilot -- Invokes --> MCPTools
  User -- Calls --> HttpApi

  BlobAct --> Blob
  EmbedAct --> AOAI
  CosmosAct --> Cosmos
  AgentAct --> AIAgents
````


## ⚙️ Getting Started (Local Development)

### Prerequisites

  * **Python 3.11**
  * **Azure Functions Core Tools v4** (`npm install -g azure-functions-core-tools@4 --unsafe-perm true` or see [official guide](https://docs.microsoft.com/azure/azure-functions/functions-run-local))
  * **Azure CLI** (`az login`)
  * **Azurite** Storage Emulator (Install via VS Code extension, npm, or [standalone](https://docs.microsoft.com/azure/storage/common/storage-use-azurite))
  * **Azure Cosmos DB Emulator** ([Windows only](https://docs.microsoft.com/azure/cosmos-db/local-emulator)) or a real Cosmos DB account.
  * **(Optional but Recommended):** VS Code Insiders with GitHub Copilot Chat extension for testing MCP tools.

### Setup & Run

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/Azure-Samples/snippy.git](https://github.com/Azure-Samples/snippy.git)
    cd snippy
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python -m venv .venv
    # Windows:
    # .venv\Scripts\activate
    # macOS/Linux:
    # source .venv/bin/activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure local settings:**

      * Copy the example settings file:
        ```bash
        cp local.settings.example.json local.settings.json
        ```
      * **Edit `local.settings.json`**:
          * `AzureWebJobsStorage`: Update with your Azurite connection string (usually `UseDevelopmentStorage=true`) or a real Azure Storage connection string.
          * `COSMOS_CONN`: Update with your Cosmos DB Emulator connection string (find in system tray icon after starting) or a real Cosmos DB connection string.
          * `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, `EMBEDDING_MODEL_DEPLOYMENT_NAME`: **Required**. Provide details for your Azure OpenAI resource and the deployment name of an embedding model (e.g., `text-embedding-3-small`). *There is no local emulator for Azure OpenAI.*
          * `PROJECT_CONNECTION_STRING`: **Required**. Provide the connection string for your Azure AI Project where the AI Agents service is configured. *There is no local emulator for Azure AI Agents.*

5.  **Start Emulators / Ensure Services Ready:**

      * Start Azurite (e.g., via VS Code command palette `Azurite: Start`).
      * Start the Azure Cosmos DB Emulator (if using).
      * Ensure your Azure OpenAI and Azure AI Project resources are deployed and accessible. You might need to configure networking if running locally.

6.  **Run the Azure Functions Host:**

    ```bash
    func start
    ```

    Your Functions app should now be running locally, typically at `http://localhost:7071`.

-----

## 🔌 Using the MCP Tools with VS Code / Copilot

1.  Ensure you have **VS Code Insiders** (latest build) and **GitHub Copilot** installed.

2.  Open the command palette (`Ctrl+Shift+P` or `⇧⌘P`).

3.  Run the command: **`MCP: Add Server`**

4.  Select **`HTTP (SSE)`**.

5.  Paste the local SSE endpoint URL: **`http://localhost:7071/runtime/webhooks/mcp/sse`**

6.  Open the **Copilot Chat** view (`Ctrl+Alt+I` or select from sidebar).

7.  Make sure you are in **Agent Mode** (often indicated by `@workspace` or similar).

8.  Try invoking the Snippy tools:

      * Select some code in your editor and type:
        > `@workspace /#save_snippet Save the selected code as 'my-first-snippet' in project 'test-proj'`
      * Ask Copilot to retrieve it:
        > `@workspace /#get_snippet Can you show me the code for the 'my-first-snippet' snippet?`
      * Ask for analysis:
        > `@workspace /#deep_research Provide a deep research analysis for the 'my-first-snippet' snippet.`
      * Ask for a style guide:
        > `@workspace /#code_style Generate a code style guide based on the 'my-first-snippet' snippet.`

    *(When deployed to Azure, replace the localhost URL with your Azure Function App's SSE endpoint and configure authentication, likely by adding your `x-functions-key` to the `mcp.json` configuration file used by the MCP extension).*

-----

## ☁️ One-Click Azure Deployment (using AZD)

The Azure Developer CLI (`azd`) provides the simplest way to provision all required Azure resources and deploy the code.

1.  **Install or Update AZD:**
    ```bash
    winget install Microsoft.Azure.DeveloperCLI
    # or: curl -fsSL [https://aka.ms/install-azd.sh](https://aka.ms/install-azd.sh) | bash
    ```
2.  **Login to Azure:**
    ```bash
    azd auth login
    ```
3.  **Provision and Deploy:**
    ```bash
    azd up
    ```
    This command will:
      * Prompt you for an environment name, subscription, and location.
      * Provision Azure Functions, Storage, Cosmos DB (with vector policy), Azure OpenAI, and Application Insights using Bicep templates (`infra/`).
      * Deploy the function app code.
      * Output the necessary endpoints, including the MCP SSE endpoint for your deployed app.

-----

## 🧪 Tests

Run the automated tests using pytest. These tests mock Azure service calls and are suitable for offline execution.

```bash
pytest -q
```

-----

## 📁 Project Layout

```plaintext
snippy/
├── .github/           # GitHub Actions workflows, issue templates, etc.
├── activities/        # Durable Function activities (Blob, Cosmos ops)
│   ├── blob_ops.py
│   └── cosmos_ops.py
├── agents/            # Wrappers for Azure AI Agents service calls
│   ├── code_style.py
│   └── deep_research.py
├── infra/             # (If using AZD) Bicep/Terraform templates for Azure resources
├── tests/             # Pytest unit/integration tests
├── .gitignore
├── azure.yaml         # (If using AZD) Azure Developer CLI configuration
├── CHANGELOG.md
├── CONTRIBUTING.md
├── function_app.py    # Main Azure Functions definitions (HTTP + MCP triggers)
├── host.json          # Functions host configuration (bundles, logging)
├── LICENSE.md
├── local.settings.json # Local development secrets (DO NOT COMMIT)
├── orchestrators.py   # Durable Function orchestrator definitions (blueprint)
├── README.md          # This file
└── requirements.txt   # Python package dependencies
```

-----

## 🤝 Contributing

Contributions are welcome\! Please follow standard fork-and-pull-request workflow.

1.  Fork the repository.
2.  Create a new branch (`git switch -c feat/your-feature`).
3.  Make your changes.
4.  Commit your changes using **Conventional Commits** (`feat: ...`, `fix: ...`, etc.).
5.  Push to your branch (`git push origin feat/your-feature`).
6.  Open a Pull Request against the `main` branch.

-----

## 📜 License

This project is licensed under the [MIT License](LICENSE.md).

