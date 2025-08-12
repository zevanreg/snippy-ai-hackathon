# Level 6 — Zero Trust Network: Private Endpoints, Managed Identity, Egress Lockdown

Goal: Secure the entire application with Zero Trust principles, private networking, and comprehensive RBAC.

## Tasks
- **Network Isolation**:
  - Deploy Function App with VNet integration
  - Implement Private Endpoints for Cosmos DB, Storage, and Key Vault
  - Configure Network Security Groups with minimal required rules
  - Enable egress lockdown with allowed service tags only
- **Identity & Access**:
  - Replace all connection strings with Managed Identity
  - Implement principle of least privilege RBAC
  - Add resource-scoped permissions (container-level, database-level)
  - Enable Azure AD authentication for Function App endpoints
- **Compliance & Monitoring**:
  - Deploy Azure Defender for all services
  - Implement network flow monitoring
  - Add compliance scanning with Azure Policy
  - Configure automated security alerts

## Infrastructure Updates
Update Bicep templates to include:
```bicep
// Private networking
virtualNetwork: {
  enabled: true
  subnetIntegration: true
  privateEndpoints: ['storage', 'cosmos', 'keyvault']
}

// Security configuration
security: {
  networkAccess: 'Private'
  managedIdentityOnly: true
  egrestLockdown: true
  defenderEnabled: true
}
```

## Acceptance
- All service-to-service communication uses private endpoints
- No public internet access from Function App (egress lockdown)
- All authentication uses Managed Identity (no secrets/keys)
- Network traffic is fully monitored and logged
- Security posture meets enterprise compliance standards

## Testing
- `tests/test_zero_trust_security.py` with network isolation tests
- Validate private endpoint connectivity
- Test RBAC enforcement and access denials
- Network traffic analysis and compliance checks

## Security Validation
- **Network**: No public IPs, all traffic through private endpoints
- **Identity**: Managed Identity for all service connections
- **Data**: Encryption in transit and at rest with customer keys
- **Monitoring**: Full audit trail of all access and changes
- **Compliance**: Azure Policy enforcement for security baselines

## Production Deployment
```bash
# Deploy with Zero Trust configuration
azd env set ZERO_TRUST_MODE true
azd env set NETWORK_ISOLATION true
azd env set PRIVATE_ENDPOINTS_ONLY true
azd up
```

## Architecture Components
- **Private DNS Zones**: Custom DNS for private endpoint resolution
- **Network Watcher**: Traffic analysis and connection monitoring
- **Azure Policy**: Automated compliance and security enforcement
- **Key Vault**: Certificate and secret management with private access
- **Defender for Cloud**: Continuous security assessment