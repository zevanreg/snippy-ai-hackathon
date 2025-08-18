# Infrastructure Reorganization for AZD

## What was changed

The infrastructure has been reorganized to follow Azure Developer CLI (AZD) conventions:

### Old Structure
```
infra/
├── levels/
│   ├── level-1/
│   │   ├── main.bicep
│   │   ├── main.json
│   │   └── resources.bicep
│   ├── level-2/ ... 
│   └── level-6/
└── README.md
```

### New Structure (AZD compliant)
```
infra/
├── main.bicep          # Main deployment entry point
├── resources.bicep     # Consolidated resources with level-based conditionals
├── modules/            # Library modules (preserved for reference)
│   ├── level-1/
│   ├── level-2/
│   └── ... level-6/
├── levels-backup/      # Backup of original structure
└── README.md
```

## Key Changes

1. **Consolidated main.bicep**: Single entry point at `infra/main.bicep` that AZD expects
2. **Consolidated resources.bicep**: All resources from levels 1-6 combined with conditional deployment based on `deploymentLevel` parameter
3. **Updated azure.yaml**: Changed from Container Apps to Azure Functions configuration
4. **Level-based deployment**: Use `deploymentLevel` parameter (1-6) to control which features are deployed

## Deployment Levels

- **Level 1**: Foundation (Cosmos DB, Function App, Storage) - `DISABLE_OPENAI=1`
- **Level 2**: AI Services (Azure AI Foundry, Embeddings, Application Insights) 
- **Level 3**: Chat capabilities (GPT-4o model deployment)
- **Level 4**: Storage orchestration (Blob containers for snippets)
- **Level 5**: Multi-agent capabilities
- **Level 6**: Zero Trust Security (Key Vault, enhanced RBAC)

## Usage

Deploy with specific level:
```bash
azd up --set deploymentLevel=2  # Deploy up to level 2
azd up --set deploymentLevel=6  # Deploy all levels (default)
```

## Verification

✅ AZD package works: `azd package`
✅ AZD provision preview works: `azd provision --preview`
✅ All Bicep resources validate correctly
✅ Conditional deployment logic tested
