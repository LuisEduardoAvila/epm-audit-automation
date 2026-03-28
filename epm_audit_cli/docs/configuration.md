# Configuration Reference

## Configuration File

Location: `config/applications.yaml`

### Structure

```yaml
# Global settings (optional)
settings:
  default_app: "fccs_prod"
  timeout: 30
  retry_attempts: 3

# Application definitions
applications:
  <app_id>:
    name: "<display name>"
    type: "<application type>"
    environment: "<environment>"
    connection:
      base_url: "<base URL>"
      region: "<cloud region>"
      tenant: "<tenant name>"
      service: "<service name>"
    authentication:
      method: "<auth method>"
      client_id: "${ENV_VAR}"
      scope: "<oauth scope>"
```

### Application Types

| Type | Description |
|------|-------------|
| `FCCS` | Oracle Financial Consolidation and Close Cloud |
| `PBCS` | Oracle Planning and Budgeting Cloud Service |
| `EDM` | Enterprise Data Management Cloud |
| `ARCS` | Account Reconciliation Cloud Service |
| `TRCS` | Tax Reporting Cloud Service |
| `NARRATIVE` | Oracle Narrative Reporting |

### Authentication Methods

#### OAuth (Recommended)

```yaml
authentication:
  method: "oauth"
  client_id: "${FCCS_CLIENT_ID}"
  client_secret: "${FCCS_CLIENT_SECRET}"
  scope: "epm.api"
  token_url: "https://identity.oraclecloud.com/oauth2/token"  # Optional
```

#### Basic Auth (Not Recommended)

```yaml
authentication:
  method: "basic"
  username: "${EPM_USERNAME}"
  password: "${EPM_PASSWORD}"
```

#### OCI Vault (Enterprise)

```yaml
authentication:
  method: "oci-vault"
  vault_id: "ocid1.vault.oc1.xxx"
  secret_id: "ocid1.secret.oc1.xxx"
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `EPM_CONFIG_PATH` | Custom config file path |
| `EPM_LOG_LEVEL` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `<APP>_CLIENT_ID` | OAuth client ID for `<APP>` |
| `<APP>_CLIENT_SECRET` | OAuth client secret for `<APP>` |
| `<APP>_USERNAME` | Username for `<APP>` |
| `<APP>_PASSWORD` | Password for `<APP>` |

### Example Configurations

#### Multi-Environment Setup

```yaml
settings:
  default_app: "fccs_prod"

applications:
  fccs_prod:
    name: "FCCS Production"
    type: "FCCS"
    environment: "production"
    connection:
      base_url: "https://company-fccs.epm.us-phoenix-1.oraclecloud.com"
    authentication:
      method: "oauth"
      client_id: "${FCCS_PROD_CLIENT_ID}"

  fccs_dev:
    name: "FCCS Development"
    type: "FCCS"
    environment: "development"
    connection:
      base_url: "https://company-fccs-dev.epm.us-phoenix-1.oraclecloud.com"
    authentication:
      method: "oauth"
      client_id: "${FCCS_DEV_CLIENT_ID}"

  fccs_test:
    name: "FCCS Test"
    type: "FCCS"
    environment: "test"
    connection:
      base_url: "https://company-fccs-test.epm.us-phoenix-1.oraclecloud.com"
    authentication:
      method: "oauth"
      client_id: "${FCCS_TEST_CLIENT_ID}"
```

#### Multi-Service Setup

```yaml
applications:
  # Financial Consolidation
  fccs:
    name: "FCCS"
    type: "FCCS"
    connection:
      base_url: "https://company-fccs.epm.us-phoenix-1.oraclecloud.com"

  # Planning
  pbcs:
    name: "Planning"
    type: "PBCS"
    connection:
      base_url: "https://company-pbcs.epm.us-phoenix-1.oraclecloud.com"

  # Enterprise Data Management
  edm:
    name: "EDM"
    type: "EDM"
    connection:
      base_url: "https://company-edm.epm.us-phoenix-1.oraclecloud.com"

  # Account Reconciliation
  arcs:
    name: "Account Reconciliation"
    type: "ARCS"
    connection:
      base_url: "https://company-arcs.epm.us-phoenix-1.oraclecloud.com"
```

### Connection Settings

```yaml
connection:
  base_url: "https://company-fccs.epm.us-phoenix-1.oraclecloud.com"
  region: "us-phoenix-1"           # Optional, for OCI integration
  tenant: "company"                 # Optional, derived from URL
  service: "fccs"                   # Optional, for service-specific logic
  
  # Connection options
  timeout: 30                       # Request timeout (seconds)
  retry_attempts: 3                  # Number of retries
  verify_ssl: true                  # SSL verification
```

### Proxy Configuration

```yaml
settings:
  proxy:
    http: "http://proxy.company.com:8080"
    https: "http://proxy.company.com:8080"
    no_proxy:
      - "localhost"
      - "*.internal.company.com"
```

### Token Caching

Tokens are cached in `~/.epm-audit/tokens/`:

```
~/.epm-audit/
├── tokens/
│   ├── fccs_prod.json
│   ├── fccs_dev.json
│   └── edm_prod.json
└── config/
    └── applications.yaml
```

Token file format:
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "expires_at": "2026-03-28T01:00:00Z",
  "token_type": "Bearer"
}
```

### Validation

Validate configuration:
```bash
epm config validate
```

Expected output:
```
✓ Configuration valid
  - Applications: 3 defined
  - fccs_prod: ✓ URL valid, ✓ Auth configured
  - fccs_dev: ✓ URL valid, ✓ Auth configured
  - edm_prod: ✓ URL valid, ✓ Auth configured
```

List applications:
```bash
epm login
```

Expected output:
```
Available Applications
┏━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ App ID     ┃ Type ┃ URL                              ┃
┡━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ fccs_prod   │ FCCS │ https://company-fccs.epm...      │
│ fccs_dev    │ FCCS │ https://company-fccs-dev.epm...  │
│ edm_prod    │ EDM  │ https://company-edm.epm...       │
└────────────┴──────┴───────────────────────────────────┘
```