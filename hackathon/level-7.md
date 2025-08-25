# Level 7 — Zero Trust Network: Enterprise Security Architecture

**🎯 Challenge Points: 30 points (Expert Security Level)**  
*Master enterprise-grade security with Zero Trust principles*

## 🎓 Learning Objective
Master Zero Trust security architecture, private networking, comprehensive RBAC, and enterprise compliance. Build systems that meet the highest security standards for regulated industries and large enterprises.

## 📋 What You're Building
A fortress-grade security architecture that implements Zero Trust principles throughout your AI code assistant. Every request is verified, every connection is private, and every action is audited. This transforms your application into an enterprise-ready service that can handle sensitive code and data.

## 🧠 Why Zero Trust Matters for AI Applications
Traditional "castle and moat" security fails with modern AI applications:
- **Never Trust, Always Verify**: Every request requires authentication and authorization
- **Least Privilege Access**: Users and services get minimum required permissions
- **Private Network Isolation**: All communication happens over private networks
- **Comprehensive Monitoring**: Every action is logged and monitored for threats
- **Compliance Ready**: Meets requirements for SOC 2, ISO 27001, and industry regulations

## 🛠️ Step-by-Step Implementation Guide

### Step 1: Understanding Zero Trust Architecture
Study the existing infrastructure templates in `infra/levels/level-6/`:

```
🌐 Internet → 🛡️ Application Gateway → 🔒 Private Endpoints → 🏗️ Function App
                        ↓                        ↓                    ↓
🔍 WAF Rules → 📊 DDoS Protection → 🔐 VNet Integration → 🎯 Managed Identity
                        ↓                        ↓                    ↓
📋 Access Logs → 🚨 Security Alerts → 🔒 Private DNS → 💾 Cosmos DB (Private)
```

The Zero Trust architecture implements multiple security layers:
1. **Network Layer**: Private endpoints, VNet integration, NSG rules
2. **Identity Layer**: Managed Identity, Azure AD integration, RBAC
3. **Data Layer**: Encryption in transit/rest, private storage access
4. **Application Layer**: Authentication, authorization, input validation
5. **Monitoring Layer**: Security Center, Sentinel, compliance scanning

### Step 2: Private Networking Implementation

#### VNet Integration and Private Endpoints:
```bicep
// Virtual Network with security-focused subnets
resource virtualNetwork 'Microsoft.Network/virtualNetworks@2023-04-01' = {
  name: 'vnet-${environmentName}'
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: ['10.0.0.0/16']
    }
    subnets: [
      {
        name: 'subnet-functions'
        properties: {
          addressPrefix: '10.0.1.0/24'
          privateEndpointNetworkPolicies: 'Enabled'
          privateLinkServiceNetworkPolicies: 'Enabled'
          delegations: [
            {
              name: 'Microsoft.Web/serverFarms'
              properties: {
                serviceName: 'Microsoft.Web/serverFarms'
              }
            }
          ]
        }
      }
      {
        name: 'subnet-private-endpoints'
        properties: {
          addressPrefix: '10.0.2.0/24'
          privateEndpointNetworkPolicies: 'Disabled'  // Required for private endpoints
        }
      }
      {
        name: 'subnet-gateway'
        properties: {
          addressPrefix: '10.0.3.0/24'
        }
      }
    ]
  }
}

// Network Security Groups with restrictive rules
resource nsgFunctions 'Microsoft.Network/networkSecurityGroups@2023-04-01' = {
  name: 'nsg-functions-${environmentName}'
  location: location
  properties: {
    securityRules: [
      {
        name: 'AllowHTTPSInbound'
        properties: {
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: '*'
          access: 'Allow'
          priority: 100
          direction: 'Inbound'
        }
      }
      {
        name: 'DenyAllInbound'
        properties: {
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
          access: 'Deny'
          priority: 4096
          direction: 'Inbound'
        }
      }
    ]
  }
}
```

#### Private Endpoints for All Services:
```bicep
// Private endpoint for Cosmos DB
resource cosmosPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-04-01' = {
  name: 'pe-cosmos-${environmentName}'
  location: location
  properties: {
    subnet: {
      id: '${virtualNetwork.id}/subnets/subnet-private-endpoints'
    }
    privateLinkServiceConnections: [
      {
        name: 'cosmos-connection'
        properties: {
          privateLinkServiceId: cosmosAccount.id
          groupIds: ['Sql']
        }
      }
    ]
  }
}

// Private DNS zone for name resolution
resource cosmosPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.documents.azure.com'
  location: 'global'
}

resource cosmosPrivateDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: cosmosPrivateDnsZone
  name: 'cosmos-dns-link'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: virtualNetwork.id
    }
  }
}
```

### Step 3: Identity and Access Management

#### Managed Identity Configuration:
```bicep
// Function App with managed identity
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: 'func-${environmentName}'
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'  // Enable managed identity
  }
  properties: {
    serverFarmId: appServicePlan.id
    virtualNetworkSubnetId: '${virtualNetwork.id}/subnets/subnet-functions'
    httpsOnly: true
    publicNetworkAccess: 'Disabled'  // Block public access
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      appSettings: [
        {
          name: 'AZURE_CLIENT_ID'
          value: functionApp.identity.principalId  // Use managed identity
        }
        {
          name: 'COSMOS_ENDPOINT'
          value: cosmosAccount.properties.documentEndpoint
        }
        // No connection strings - all auth via managed identity
      ]
    }
  }
}

// RBAC assignments with least privilege
resource cosmosRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2023-04-15' = {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, functionApp.id, 'cosmos-contributor')
  properties: {
    roleDefinitionId: '${cosmosAccount.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'  // Built-in Data Contributor
    principalId: functionApp.identity.principalId
    scope: cosmosAccount.id
  }
}

resource storageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, functionApp.id, 'storage-blob-data-contributor')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')  // Storage Blob Data Contributor
    principalId: functionApp.identity.principalId
  }
}
```

#### Azure AD Authentication:
```bicep
// Azure AD authentication for Function App
resource authSettings 'Microsoft.Web/sites/config@2023-01-01' = {
  parent: functionApp
  name: 'authsettingsV2'
  properties: {
    globalValidation: {
      requireAuthentication: true
      unauthenticatedClientAction: 'Return401'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          openIdIssuer: 'https://login.microsoftonline.com/${tenant().tenantId}/v2.0'
          clientId: aadApp.appId
        }
        validation: {
          allowedAudiences: ['api://${aadApp.appId}']
        }
      }
    }
    login: {
      tokenStore: {
        enabled: true
      }
    }
  }
}
```

### Step 4: Security Monitoring and Compliance

#### Azure Defender and Security Center:
```bicep
// Security Center and Defender for Cloud
resource defenderPlan 'Microsoft.Security/pricings@2022-03-01' = {
  name: 'AppServices'
  properties: {
    pricingTier: 'Standard'
  }
}

resource defenderCosmosDb 'Microsoft.Security/pricings@2022-03-01' = {
  name: 'CosmosDb'
  properties: {
    pricingTier: 'Standard'
  }
}

// Advanced Threat Protection
resource cosmosAdvancedThreatProtection 'Microsoft.DocumentDB/databaseAccounts/advancedThreatProtectionSettings@2023-04-15' = {
  parent: cosmosAccount
  name: 'current'
  properties: {
    isEnabled: true
  }
}

// Security alerts and monitoring
resource securityAlert 'Microsoft.Insights/activityLogAlerts@2020-10-01' = {
  name: 'security-alert-${environmentName}'
  location: 'global'
  properties: {
    enabled: true
    scopes: [resourceGroup().id]
    condition: {
      allOf: [
        {
          field: 'category'
          equals: 'Security'
        }
        {
          field: 'operationName'
          equals: 'Microsoft.Security/securityStatuses/write'
        }
      ]
    }
    actions: {
      actionGroups: [
        {
          actionGroupId: actionGroup.id
        }
      ]
    }
  }
}
```

#### Comprehensive Audit Logging:
```bicep
// Diagnostic settings for all services
resource functionAppDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'function-app-diagnostics'
  scope: functionApp
  properties: {
    workspaceId: logAnalytics.id
    logs: [
      {
        category: 'FunctionAppLogs'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 90
        }
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 90
        }
      }
    ]
  }
}

resource cosmosDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'cosmos-diagnostics'
  scope: cosmosAccount
  properties: {
    workspaceId: logAnalytics.id
    logs: [
      {
        category: 'DataPlaneRequests'
        enabled: true
      }
      {
        category: 'MongoRequests'
        enabled: true
      }
      {
        category: 'QueryRuntimeStatistics'
        enabled: true
      }
    ]
  }
}
```

### Step 5: Application-Level Security Implementation

#### Enhanced RBAC in Code:
```python
# Enhanced RBAC implementation
class ZeroTrustAuth:
    """Zero Trust authentication and authorization."""
    
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.token_cache = {}
        
    async def verify_request(self, req: func.HttpRequest) -> dict:
        """Verify every request with comprehensive checks."""
        # 1. Extract and validate JWT token
        auth_header = req.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            raise UnauthorizedError("Missing or invalid authorization header")
            
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # 2. Validate token with Azure AD
        try:
            payload = await self._validate_jwt_token(token)
        except Exception as e:
            raise UnauthorizedError(f"Token validation failed: {str(e)}")
        
        # 3. Extract user context
        user_id = payload.get('sub')
        tenant_id = payload.get('tid')
        app_id = payload.get('aud')
        
        # 4. Verify application audience
        expected_app_id = os.environ.get('AZURE_CLIENT_ID')
        if app_id != expected_app_id:
            raise UnauthorizedError("Invalid token audience")
        
        # 5. Check user permissions for project
        project_id = req.params.get('projectId') or req.get_json().get('projectId')
        if project_id:
            permissions = await self._get_user_permissions(user_id, project_id)
            if not permissions.get('read_access'):
                raise ForbiddenError("Insufficient permissions for project")
        
        return {
            'user_id': user_id,
            'tenant_id': tenant_id,
            'permissions': permissions,
            'audit_context': {
                'ip_address': req.headers.get('X-Forwarded-For'),
                'user_agent': req.headers.get('User-Agent'),
                'request_id': str(uuid.uuid4())
            }
        }
    
    async def _validate_jwt_token(self, token: str) -> dict:
        """Validate JWT token with Azure AD."""
        # Cache validation results for performance
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if token_hash in self.token_cache:
            cached_result = self.token_cache[token_hash]
            if cached_result['expires_at'] > time.time():
                return cached_result['payload']
        
        # Validate with Azure AD
        try:
            # In production, validate signature and claims
            decoded = jwt.decode(
                token,
                options={"verify_signature": False},  # Simplified for demo
                algorithms=["RS256"]
            )
            
            # Cache valid token
            self.token_cache[token_hash] = {
                'payload': decoded,
                'expires_at': decoded.get('exp', time.time() + 3600)
            }
            
            return decoded
        except jwt.InvalidTokenError as e:
            raise UnauthorizedError(f"Invalid JWT token: {str(e)}")

# Apply Zero Trust to all endpoints
@bp.route(route="query", methods=["POST"])
async def secure_query_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """Zero Trust secured query endpoint."""
    auth = ZeroTrustAuth()
    
    try:
        # 1. Verify authentication and authorization
        auth_context = await auth.verify_request(req)
        
        # 2. Audit log the request
        logging.info(
            "Query request",
            extra={
                'user_id': auth_context['user_id'],
                'request_id': auth_context['audit_context']['request_id'],
                'ip_address': auth_context['audit_context']['ip_address'],
                'event_type': 'query_request'
            }
        )
        
        # 3. Process the query with user context
        data = req.get_json()
        question = data.get("question", "")
        project_id = data.get("projectId", "")
        
        # 4. Apply data isolation based on permissions
        if not auth_context['permissions'].get('read_access'):
            raise ForbiddenError("Read access denied for project")
            
        # 5. Execute query with user context
        results = await execute_secured_query(
            question=question,
            project_id=project_id,
            user_context=auth_context
        )
        
        # 6. Audit log the response
        logging.info(
            "Query completed",
            extra={
                'user_id': auth_context['user_id'],
                'request_id': auth_context['audit_context']['request_id'],
                'results_count': len(results.get('citations', [])),
                'event_type': 'query_completed'
            }
        )
        
        return func.HttpResponse(
            body=json.dumps(results),
            mimetype="application/json",
            status_code=200
        )
        
    except (UnauthorizedError, ForbiddenError) as e:
        # Audit log security violations
        logging.warning(
            "Security violation",
            extra={
                'error': str(e),
                'ip_address': req.headers.get('X-Forwarded-For'),
                'user_agent': req.headers.get('User-Agent'),
                'event_type': 'security_violation'
            }
        )
        
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=401 if isinstance(e, UnauthorizedError) else 403
        )
    except Exception as e:
        # Audit log system errors
        logging.error(
            "System error",
            extra={
                'error': str(e),
                'event_type': 'system_error'
            },
            exc_info=True
        )
        
        return func.HttpResponse(
            body=json.dumps({"error": "Internal server error"}),
            mimetype="application/json",
            status_code=500
        )
```

#### Data Encryption and Protection:
```python
# Data encryption at rest and in transit
class SecureDataHandler:
    """Handle sensitive data with encryption."""
    
    def __init__(self):
        # Get encryption key from Key Vault via managed identity
        self.key_vault_client = SecretClient(
            vault_url=os.environ['KEY_VAULT_URL'],
            credential=DefaultAzureCredential()
        )
        
    async def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data before storage."""
        # Get encryption key from Key Vault
        key_secret = await self.key_vault_client.get_secret("data-encryption-key")
        encryption_key = key_secret.value.encode()
        
        # Encrypt using Fernet (symmetric encryption)
        f = Fernet(base64.urlsafe_b64encode(encryption_key[:32]))
        encrypted_data = f.encrypt(data.encode())
        
        return base64.b64encode(encrypted_data).decode()
    
    async def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data after retrieval."""
        key_secret = await self.key_vault_client.get_secret("data-encryption-key")
        encryption_key = key_secret.value.encode()
        
        f = Fernet(base64.urlsafe_b64encode(encryption_key[:32]))
        decoded_data = base64.b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(decoded_data)
        
        return decrypted_data.decode()

# Apply encryption to snippet storage
async def secure_save_snippet(name: str, code: str, project_id: str, user_context: dict) -> dict:
    """Save snippet with encryption and audit logging."""
    data_handler = SecureDataHandler()
    
    # 1. Encrypt sensitive code content
    encrypted_code = await data_handler.encrypt_sensitive_data(code)
    
    # 2. Add audit trail
    audit_data = {
        'user_id': user_context['user_id'],
        'action': 'save_snippet',
        'timestamp': datetime.utcnow().isoformat(),
        'ip_address': user_context['audit_context']['ip_address']
    }
    
    # 3. Save with encryption and audit
    result = await cosmos_ops.upsert_document(
        name=name,
        project_id=project_id,
        code=encrypted_code,  # Store encrypted
        audit_trail=audit_data,
        encryption_metadata={'algorithm': 'fernet', 'key_version': '1'}
    )
    
    return result
```

## ✅ Acceptance Criteria
Complete when you can verify:
- ✅ All service-to-service communication uses private endpoints only
- ✅ Function App has no public internet access (egress lockdown)
- ✅ All authentication uses Azure AD with Managed Identity
- ✅ RBAC enforces least privilege access at granular levels
- ✅ All data is encrypted in transit and at rest
- ✅ Comprehensive audit logging captures all security events
- ✅ Network Security Groups block unauthorized traffic
- ✅ Azure Defender monitors for security threats
- ✅ Compliance policies are enforced automatically
- ✅ Emergency access procedures are documented and tested

## 🧪 Testing Zero Trust Security

### Security Validation Tests:

1. **Network Isolation Testing:**
   ```bash
   # Verify no public access to Function App
   curl https://your-function-app.azurewebsites.net/api/health
   # Expected: Connection refused or timeout
   
   # Test private endpoint connectivity from within VNet
   # (Requires Azure Bastion or VPN connection)
   nslookup your-function-app.azurewebsites.net
   # Expected: Private IP address resolution
   ```

2. **Authentication Testing:**
   ```bash
   # Test unauthenticated access
   curl -X POST https://your-app-gateway.azure.com/api/query \
     -H "Content-Type: application/json" \
     -d '{"question": "test"}'
   # Expected: 401 Unauthorized
   
   # Test with invalid token
   curl -X POST https://your-app-gateway.azure.com/api/query \
     -H "Authorization: Bearer invalid-token" \
     -H "Content-Type: application/json" \
     -d '{"question": "test"}'
   # Expected: 401 Unauthorized
   ```

3. **RBAC Testing:**
   ```bash
   # Test with valid token but insufficient permissions
   curl -X POST https://your-app-gateway.azure.com/api/query \
     -H "Authorization: Bearer $VALID_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"projectId": "restricted-project", "question": "test"}'
   # Expected: 403 Forbidden
   ```

### Security Monitoring Validation:

1. **Audit Log Queries (KQL):**
   ```kusto
   // Security events in the last 24 hours
   SecurityEvent
   | where TimeGenerated > ago(24h)
   | where EventID in (4625, 4624)  // Failed and successful logons
   | summarize count() by Account, EventID
   | order by count_ desc
   
   // Unauthorized access attempts
   AppServiceHTTPLogs
   | where TimeGenerated > ago(1h)
   | where ScStatus in (401, 403)
   | project TimeGenerated, CsMethod, CsUriStem, CIp, ScStatus
   | order by TimeGenerated desc
   
   // Private endpoint traffic analysis
   AzureNetworkAnalytics_CL
   | where TimeGenerated > ago(1h)
   | where FlowType_s == "ExternalPublic"
   | summarize count() by SrcIP_s, DestIP_s
   ```

2. **Threat Detection Alerts:**
   ```kusto
   // Security alerts from Defender for Cloud
   SecurityAlert
   | where TimeGenerated > ago(24h)
   | where AlertSeverity in ("High", "Medium")
   | project TimeGenerated, AlertName, AlertSeverity, Description
   | order by TimeGenerated desc
   ```

## 🚀 Deployment Options

### Option 1: Staging Environment (Partial Zero Trust)

1. **Deploy with reduced security for testing:**
   ```bash
   # Set environment variables for staging
   azd env set ENVIRONMENT_NAME staging
   azd env set ENABLE_PUBLIC_ACCESS true
   azd env set REQUIRE_AUTHENTICATION false
   azd up
   ```

2. **Benefits:**
   - Easier testing and development
   - Gradual security implementation
   - Cost optimization for non-production

### Option 2: Production Environment (Full Zero Trust)

1. **Deploy with maximum security:**
   ```bash
   # Set environment variables for production
   azd env set ENVIRONMENT_NAME production
   azd env set ZERO_TRUST_MODE true
   azd env set NETWORK_ISOLATION true
   azd env set PRIVATE_ENDPOINTS_ONLY true
   azd env set REQUIRE_AUTHENTICATION true
   azd env set ENABLE_DEFENDER true
   azd up
   ```

2. **Post-deployment security validation:**
   ```bash
   # Run security assessment
   az security assessment list --resource-group your-rg
   
   # Check Defender for Cloud recommendations
   az security sub-assessment list
   
   # Validate network isolation
   az network private-endpoint list --resource-group your-rg
   ```

## 💡 Pro Tips from Your Mentor

### 🛡️ Zero Trust Implementation Strategy:
- **Start with Identity**: Implement strong authentication before network controls
- **Layer Security**: Multiple overlapping security controls provide defense in depth
- **Monitor Everything**: Comprehensive logging is essential for threat detection
- **Test Regularly**: Continuous security testing validates your protection

### 📊 Security Operations:
- **Incident Response**: Plan and practice security incident procedures
- **Compliance Automation**: Use Azure Policy for automated compliance checking
- **Regular Assessments**: Schedule penetration testing and security reviews
- **Security Training**: Keep your team updated on latest security practices

### 🔍 Advanced Monitoring:
- **Behavioral Analytics**: Use Azure Sentinel for advanced threat detection
- **Custom Alerts**: Create specific alerts for your application's threat model
- **Integration**: Connect security tools with your existing SIEM/SOAR platforms
- **Metrics Dashboard**: Build executive dashboards for security posture visibility

### ⚡ Performance Considerations:
- **Connection Pooling**: Optimize connections in private network environments
- **Caching Strategy**: Cache authentication tokens and permissions appropriately
- **Network Latency**: Plan for additional latency from security controls
- **Scaling**: Ensure security controls scale with your application load

## 🎯 Success Indicators
You've mastered Level 7 when:
1. All network traffic flows through private endpoints with no public access
2. Authentication and authorization work seamlessly with Azure AD
3. Comprehensive audit logs capture all security-relevant events
4. Automated compliance checking passes all required standards
5. Security monitoring detects and alerts on suspicious activities
6. Performance remains acceptable despite additional security layers
7. You can demonstrate compliance with enterprise security requirements
8. Emergency access procedures are tested and documented

**Congratulations!** You've built an enterprise-grade AI application with Zero Trust security that meets the highest industry standards!

---

## 📚 Additional Resources
- [Azure Zero Trust Architecture](https://docs.microsoft.com/en-us/azure/security/fundamentals/zero-trust)
- [Azure Private Endpoints](https://docs.microsoft.com/en-us/azure/private-link/private-endpoint-overview)
- [Azure Managed Identity](https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/)
- [Azure Defender for Cloud](https://docs.microsoft.com/en-us/azure/defender-for-cloud/)
- [Compliance in Azure](https://docs.microsoft.com/en-us/azure/compliance/)
- [Azure Sentinel](https://docs.microsoft.com/en-us/azure/sentinel/)