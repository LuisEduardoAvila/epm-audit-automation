# Credential Management System

*Secure OAuth-based credential management for EPM applications*

## Overview

The credential management system provides:
- **Centralized configuration** for all EPM apps in `applications.yaml`
- **Secure credential storage** (OCI Vault, keyring, or environment variables)
- **OAuth 2.0 token sharing** across application suites (prod/test/dev)
- **Environment isolation** (strict separation of production, test, development)
- **Extensible architecture** (add any EPM app type, current or future)

---

## Quick Start

### 1. Configuration

Edit `config/applications.yaml`:

```yaml
applications:
  fccs_prod:
    name: "FCCS Production"
    type: "FCCS"
    environment: "production"
    
    connection:
      base_url: "https://your-company-fccs.epm.us-phoenix-1.oraclecloud.com"
      region: "us-phoenix-1"
      tenant: "your-company"
      service: "fccs"
    
    authentication:
      method: "oauth2"
      credential_ref: "oci_vault://epm-oauth-production"
      token_scope: "production_suite"  # 🔄 Shared across prod apps
      
    metadata:
      description: "Financial Consolidation - Global"
      owner: "finance-team@company.com"
      criticality: "high"
      sox_relevant: true
```

### 2. Store Credentials

#### Option A: OCI Vault (Production Recommended)

```bash
# Create secrets in OCI Vault
oci vault secret create \
  --compartment-id ocid1.compartment.xxx \
  --secret-name epm-oauth-production-client-id \
  --secret-content-content "your-client-id"

oci vault secret create \
  --compartment-id ocid1.compartment.xxx \
  --secret-name epm-oauth-production-client-secret \
  --secret-content-content "your-client-secret"
```

#### Option B: Environment Variables (Development)

```bash
export EPM_OAUTH_PRODUCTION_CLIENT_ID="your-client-id"
export EPM_OAUTH_PRODUCTION_CLIENT_SECRET="your-client-secret"
export EPM_OAUTH_PRODUCTION_TOKEN_URL="https://idcs-xxx.identity.oraclecloud.com/oauth2/v1/token"
```

#### Option C: Keyring (Secure Local)

```bash
python scripts/credential_manager.py --config config/applications.yaml
# Or use keyring CLI
keyring set epm-audit-automation oauth-client-id
```

### 3. List Applications

```bash
# List all configured apps
python scripts/credential_manager.py list-apps

# Filter by environment
python scripts/credential_manager.py list-apps --env production

# Filter by type
python scripts/credential_manager.py list-apps --type FCCS
```

Output:
```
Configured Applications:
--------------------------------------------------------------------------------
ID                   Name                           Type            Env       
--------------------------------------------------------------------------------
fccs_prod            FCCS Production                FCCS            production
pbcs_prod            PBCS Production                PBCS            production
edm_prod             EDM Production                 EDM             production
fccs_test            FCCS Test                      FCCS            test
dev_fccs             FCCS Development               FCCS            development
```

### 4. Test Connection

```bash
# Get connection info
python scripts/credential_manager.py get-connection fccs_prod

# Test OAuth token retrieval
python scripts/credential_manager.py test-oauth fccs_prod
```

### 5. Use in Scripts

```python
from scripts.credential_manager import CredentialManager

# Initialize
manager = CredentialManager('config/applications.yaml')

# Get OAuth token (automatically cached and refreshed)
token = manager.get_oauth_token('fccs_prod')

# Get connection URL
base_url = manager.get_connection_url('fccs_prod')

# Get HTTP headers with auth
headers = manager.get_headers('fccs_prod')

# Make API call
import requests
response = requests.get(
    f"{base_url}/interop/rest/v1/applications",
    headers=headers
)
```

---

## Architecture

### OAuth Token Sharing

```
Production Suite OAuth
├── fccs_prod (shares token)
├── pbcs_prod (shares token)
├── edm_prod (shares token)
├── dataexchange_prod (shares token)
└── arcs_prod (shares token)

Test Suite OAuth
├── fccs_test (shares token)
├── pbcs_test (shares token)
└── edm_test (shares token)

Development OAuth
├── fccs_dev (shares token)
└── pbcs_dev (shares token)
```

**Benefits:**
- Single OAuth token per environment suite
- Automatic refresh when expired
- Reduced API calls to identity provider
- Centralized credential rotation

### Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Configuration (applications.yaml)                          │
│  - App definitions                                          │
│  - Connection metadata (URLs, regions)                        │
│  - Credential references (not actual secrets)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Credential Backend (pluggable)                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ OCI Vault   │  │ OS Keyring   │  │ Environment  │       │
│  │ (prod)      │  │ (dev/test)   │  │ (dev only)   │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  OAuth Token Manager                                        │
│  - Fetches tokens from IdP                                  │
│  - Caches tokens (encrypted at rest)                      │
│  - Auto-refresh before expiry                             │
│  - Shared across app suite                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration Reference

### Application Definition

```yaml
applications:
  {app_id}:              # Unique identifier (e.g., fccs_prod)
    name: str            # Display name
    type: str            # Application type (FCCS, PBCS, EDM, etc.)
    environment: str     # production | test | development
    
    connection:
      base_url: str      # Full instance URL
      region: str        # OCI region
      tenant: str        # Tenant name (optional)
      service: str       # Service identifier (optional)
    
    authentication:
      method: oauth2      # OAuth 2.0 (only method supported)
      credential_ref: str  # Reference to stored credentials
      token_scope: str   # OAuth scope for token sharing
      
    metadata:
      description: str   # Human-readable description
      owner: str         # Team/individual responsible
      criticality: str   # critical | high | medium | low
      sox_relevant: bool # SOX compliance flag
```

### OAuth Scope Configuration

```yaml
oauth:
  {scope_name}:
    name: str            # Display name
    token_url: str       # IdP token endpoint
    client_id_ref: str   # Reference to client ID secret
    client_secret_ref: str # Reference to client secret
    scope: str           # OAuth scope string
    applications: []     # List of app IDs using this scope
```

### Environment Definitions

```yaml
environments:
  production:
    name: str
    description: str
    security_level: high | medium | low
    change_control: strict | standard | relaxed
    sox_relevant: bool
    backup_required: bool
    
  test:
    # Same structure
    
  development:
    # Same structure
```

### Application Types

```yaml
types:
  FCCS:
    name: str
    modules: []          # Supported modules/features
    audit_endpoints: []  # Available audit APIs
    
  # Add custom types as needed
  CUSTOM_APP:
    name: str
    modules: []
    audit_endpoints: []
```

---

## Usage Examples

### Example 1: Get All Production Apps

```python
manager = CredentialManager('config/applications.yaml')

# Get all production app IDs
prod_apps = manager.get_applications_by_environment('production')
print(f"Production apps: {prod_apps}")
# Output: ['fccs_prod', 'pbcs_prod', 'edm_prod', ...]

# Loop and audit each
for app_id in prod_apps:
    if manager.is_sox_relevant(app_id):
        token = manager.get_oauth_token(app_id)
        # Run SOX audit...
```

### Example 2: Filter by Type

```python
# Get all FCCS instances
fccs_apps = manager.get_applications_by_type('FCCS')

for app_id in fccs_apps:
    app = manager.get_application(app_id)
    print(f"{app['name']} ({app['environment']})")
    # Output:
    # FCCS Production (production)
    # FCCS Test (test)
    # FCCS Development (development)
```

### Example 3: Cross-Environment Comparison

```python
# Get FCCS config from all environments
for env in ['production', 'test', 'development']:
    app_id = f'fccs_{env}'
    try:
        app = manager.get_application(app_id)
        url = manager.get_connection_url(app_id)
        print(f"{env}: {url}")
    except KeyError:
        print(f"{env}: Not configured")
```

### Example 4: Bulk Audit with Shared Token

```python
# All prod apps share same OAuth token
prod_apps = manager.get_applications_by_environment('production')
token = manager.get_oauth_token(prod_apps[0])  # Fetch once

# Reuse for all (token manager caches automatically)
for app_id in prod_apps:
    headers = manager.get_headers(app_id)
    # Each call returns same cached token
```

---

## Security Best Practices

### 1. Credential Storage

| Environment | Backend | Reason |
|-------------|---------|--------|
| Production | OCI Vault | Enterprise-grade, audit logging, rotation |
| Test | Keyring | Secure local storage |
| Development | Environment | Easy rotation, disposable |

### 2. OAuth Handling

✅ **DO:**
- Use OAuth 2.0 Client Credentials flow
- Store tokens in memory only
- Encrypt token cache at rest
- Refresh tokens before expiry
- Invalidate tokens on scope changes

❌ **DON'T:**
- Hardcode credentials in scripts
- Store tokens in version control
- Log token values
- Share tokens across environments

### 3. Environment Isolation

✅ **DO:**
- Separate OAuth scopes per environment
- Different client IDs per environment
- Strict firewall rules between environments
- Audit all token usage

❌ **DON'T:**
- Share production tokens with test
- Use production credentials in dev
- Copy-paste tokens between configs

### 4. Credential Rotation

```bash
# 1. Update secret in backend (OCI Vault/Keyring)
oci vault secret update --secret-id ocid1.vaultsecret... --secret-content-content "new-value"

# 2. Invalidate cached tokens
# Token manager will fetch new token automatically

# 3. Test connectivity
python scripts/credential_manager.py test-oauth fccs_prod
```

---

## Troubleshooting

### "OCI Vault unavailable"

```bash
# Install OCI SDK
pip install oci

# Configure OCI CLI
oci setup config

# Verify connectivity
oci vault secret list --compartment-id ocid1.compartment.xxx
```

### "Token refresh failed"

```bash
# Check token URL
curl -X POST \
  https://idcs-xxx.identity.oraclecloud.com/oauth2/v1/token \
  -d "grant_type=client_credentials" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET"

# Clear token cache
rm ~/.epm_audit/oauth_tokens.json
```

### "Application not found"

```bash
# Verify config
cat config/applications.yaml | grep fccs_prod

# List all apps
python scripts/credential_manager.py list-apps
```

---

## Adding New Applications

### Step 1: Add to applications.yaml

```yaml
applications:
  my_new_app_prod:
    name: "My New App Production"
    type: "CUSTOM"  # Or existing type
    environment: "production"
    
    connection:
      base_url: "https://..."
      region: "us-ashburn-1"
    
    authentication:
      method: "oauth2"
      credential_ref: "oci_vault://epm-oauth-production"
      token_scope: "production_suite"
      
    metadata:
      description: "Custom EPM Application"
      owner: "team@company.com"
      criticality: "medium"
      sox_relevant: false
```

### Step 2: Add Type Definition (if new)

```yaml
types:
  CUSTOM:
    name: "Custom EPM App"
    modules:
      - custom_feature_1
      - custom_feature_2
    audit_endpoints:
      - custom_audit_api
```

### Step 3: Verify

```bash
python scripts/credential_manager.py list-apps | grep my_new_app
python scripts/credential_manager.py test-oauth my_new_app_prod
```

---

*Last Updated: February 26, 2026*
*Status: Production-ready*
