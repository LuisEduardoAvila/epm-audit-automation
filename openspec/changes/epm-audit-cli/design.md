# Design: EPM Audit CLI

## Overview

The EPM Audit CLI (`epm`) fills gaps in Oracle's EPM Automate for SOX audit workflows. It provides commands for:

1. **Artifact change tracking** — Query configuration changes
2. **EDM request history** — Metadata deployment audit
3. **Business rule inspection** — Extract and diff rule logic
4. **OCI infrastructure** — Monitor compute/storage/networking

Built on existing `credential_manager.py` for authentication, using Click for CLI framework.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Layer (Click)                       │
│  epm login | artifact-changes | edm-requests | rule-diff     │
│  epm oci-instances | oci-storage | oci-network               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Client Layer                          │
│  ┌─────────────┐ ┌─────────────┐ ┌────────────────────────┐ │
│  │ EPM Client  │ │ EDM Client  │ │ OCI Client (optional)  │ │
│  │ (FCCS/PBCS) │ │             │ │                        │ │
│  └─────────────┘ └─────────────┘ └────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Authentication Layer                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ credential_manager.py (existing)                     │   │
│  │ - OAuth 2.0 token management                         │   │
│  │ - OCI Vault backend                                  │   │
│  │ - Token caching & refresh                            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               Configuration (applications.yaml)             │
│  - Application URLs                                        │
│  - OAuth scopes                                            │
│  - Environment metadata                                    │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Details

### Project Structure

```
epm_audit_cli/
├── __init__.py
├── cli.py                 # Click CLI entry point
├── commands/
│   ├── __init__.py
│   ├── login.py           # epm login
│   ├── artifact.py        # epm artifact-changes
│   ├── edm.py             # epm edm-requests, edm-violations
│   ├── rules.py           # epm rules, rule-diff
│   ├── oci.py             # epm oci-instances, oci-storage, oci-network
│   └── iam.py             # epm iam-users, iam-groups, iam-memberships, iam-access-review
├── clients/
│   ├── __init__.py
│   ├── base.py            # Base API client
│   ├── epm.py             # EPM Cloud client
│   ├── edm.py             # EDM client
│   ├── oci_client.py      # OCI client (optional)
│   └── iam.py             # OCI IAM/IDCS client
├── output/
│   ├── __init__.py
│   ├── table.py           # Table formatter
│   ├── json_fmt.py        # JSON formatter
│   └── csv_fmt.py         # CSV formatter
├── config/
│   ├── __init__.py
│   └── loader.py          # Config loader (uses applications.yaml)
└── utils/
    ├── __init__.py
    ├── dates.py           # Date parsing utilities
    ├── classify.py        # Material/operational classification
    └── access_review.py   # SOX access review utilities (dormant, privileged, SoD)
```

### CLI Framework: Click

**Why Click over argparse:**
- Decorator-based command definition
- Automatic help generation
- Built-in type validation
- Color support via Click + Rich
- Subcommand groups

**Example Command Structure:**
```python
import click

@click.group()
def cli():
    """EPM Audit CLI - Oracle EPM audit operations"""
    pass

@cli.command()
@click.option('--app', required=True, help='Application ID from config')
@click.option('--from', 'from_date', required=True, help='Start date (YYYY-MM-DD)')
@click.option('--to', 'to_date', required=True, help='End date (YYYY-MM-DD)')
@click.option('--type', 'artifact_types', multiple=True, help='Filter by artifact type')
@click.option('--output', type=click.Choice(['table', 'json', 'csv']), default='table')
def artifact_changes(app, from_date, to_date, artifact_types, output):
    """Query artifact modification history"""
    # Implementation
    pass
```

### API Client Pattern

**Base Client:**
```python
class BaseAPIClient:
    def __init__(self, base_url: str, credential_manager: CredentialManager, app_id: str):
        self.base_url = base_url.rstrip('/')
        self.creds = credential_manager
        self.app_id = app_id
        self.session = requests.Session()
        
    def _get_headers(self) -> Dict[str, str]:
        token = self.creds.get_oauth_token(self.app_id)
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        response = self.session.request(
            method, url, headers=headers, **kwargs
        )
        
        # Handle rate limiting
        if response.status_code == 429:
            return self._handle_rate_limit(response, method, endpoint, **kwargs)
        
        response.raise_for_status()
        return response.json()
    
    def _handle_rate_limit(self, response, method, endpoint, **kwargs):
        # Exponential backoff
        retry_after = int(response.headers.get('Retry-After', 5))
        time.sleep(retry_after)
        return self._request(method, endpoint, **kwargs)
```

**EPM Client:**
```python
class EPMClient(BaseAPIClient):
    def get_artifact_modifications(
        self, 
        from_date: str, 
        to_date: str,
        artifact_types: List[str] = None,
        modified_by: str = None
    ) -> List[Dict]:
        endpoint = f"/interop/rest/v1/applications/{self.app_id}/artifact-modification"
        params = {
            'startDate': from_date,
            'endDate': to_date
        }
        if artifact_types:
            params['artifactTypes'] = ','.join(artifact_types)
        if modified_by:
            params['modifiedBy'] = modified_by
            
        return self._paginated_request('GET', endpoint, params)
```

**IAM Client:**
```python
class IAMClient:
    """OCI Identity and Access Management client for IDCS user/group queries."""
    
    def __init__(self, config: dict):
        from oci.identity import IdentityClient
        self.client = IdentityClient(config)
        self.compartment_id = config.get('tenancy')
    
    def list_users(self, compartment_id: str = None) -> List[Dict]:
        """List all users in compartment."""
        users = self.client.list_users(
            compartment_id=compartment_id or self.compartment_id
        )
        return [self._enrich_user(u) for u in users.data]
    
    def list_groups(self, compartment_id: str = None) -> List[Dict]:
        """List all groups in compartment."""
        groups = self.client.list_groups(
            compartment_id=compartment_id or self.compartment_id
        )
        return [{'name': g.name, 'id': g.id} for g in groups.data]
    
    def get_group_memberships(self, compartment_id: str, group_id: str) -> List[str]:
        """Get user IDs for group members."""
        memberships = self.client.list_user_group_memberships(
            compartment_id=compartment_id,
            group_id=group_id
        )
        return [m.user_id for m in memberships.data]
    
    def get_access_review(self, compartment_id: str) -> Dict:
        """Generate comprehensive access review for SOX audit."""
        users = self.list_users(compartment_id)
        groups = self.list_groups(compartment_id)
        
        # Build group membership map
        memberships = {}
        for group in groups:
            memberships[group['name']] = self.get_group_memberships(
                compartment_id, group['id']
            )
        
        return {
            'users': users,
            'groups': groups,
            'memberships': memberships,
            'service_accounts': [u for u in users if self._is_service_account(u)],
            'privileged_users': [u for u in users if self._is_privileged(u, memberships)],
            'dormant_accounts': [u for u in users if self._is_dormant(u)]
        }
    
    def _is_service_account(self, user: Dict) -> bool:
        return user.get('name', '').startswith(('epm-', 'svc-', 'automation-'))
    
    def _is_dormant(self, user: Dict, days: int = 90) -> bool:
        last_login = user.get('last_login_time')
        if not last_login:
            return True  # Never logged in
        from datetime import datetime, timedelta
        threshold = datetime.now() - timedelta(days=days)
        return last_login < threshold
    
    def _is_privileged(self, user: Dict, memberships: Dict) -> bool:
        admin_groups = {'Administrators', 'IDCSAdministrators', 'SecurityAdmins'}
        user_id = user.get('id')
        for group_name, member_ids in memberships.items():
            if group_name in admin_groups and user_id in member_ids:
                return True
        return False
```

### Classification Logic

**Material vs Operational:**
```python
# From extract-artifact-changes.py patterns
OPERATIONAL_TYPES = {
    'PERIOD', 'PERIOD_STATUS', 'JOB', 'CONSOLIDATION_EXECUTION',
    'JOURNAL_POSTING', 'FORM_SAVE', 'DATA_ENTRY', 'CALCULATION_RUN',
    'APPROVAL_PROMOTION', 'REQUEST_APPROVAL', 'SNAPSHOT_RESTORE',
    'BACKUP', 'REPLICATION'
}

CONFIGURATION_TYPES = {
    'CONSOLIDATION_RULE', 'BUSINESS_RULE', 'CALCULATION_RULE',
    'DATA_FORM', 'COMPOSITE_FORM', 'DIMENSION', 'ATTRIBUTE',
    'SMART_LIST', 'SUBSTITUTION_VARIABLE', 'CURRENCY_TABLE',
    'ALLOCATION_RULE', 'RECONCILIATION_FORMAT', 'MATCHING_RULE',
    'VALIDATION_RULE', 'DATA_LOAD_RULE', 'IMPORT_FORMAT'
}

def classify_change(artifact: Dict) -> str:
    artifact_type = artifact.get('artifactType', '').upper()
    
    if artifact_type in OPERATIONAL_TYPES:
        return 'OPERATIONAL'
    elif artifact_type in CONFIGURATION_TYPES:
        return 'MATERIAL'
    else:
        return 'REVIEW_REQUIRED'
```

### Output Formatters

**Table Output (Rich):**
```python
from rich.console import Console
from rich.table import Table

def format_table(data: List[Dict], columns: List[str]) -> str:
    console = Console()
    table = Table(show_header=True, header_style="bold")
    
    for col in columns:
        table.add_column(col)
    
    for row in data:
        table.add_row(*[str(row.get(col.lower(), '')) for col in columns])
    
    console.print(table)
```

**JSON Output:**
```python
import json

def format_json(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)
```

### Authentication Flow

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│  CLI Command │────▶│ CredentialManager│────▶│  OCI Vault  │
└─────────────┘     └─────────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │ OAuth Token Cache│
                    │ (~/.epm-audit/)  │
                    └─────────────────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │ Token Valid?    │
                    └─────────────────┘
                      │           │
                     Yes          No
                      │           │
                      ▼           ▼
                 ┌─────────┐  ┌───────────────┐
                 │ Return  │  │ Refresh Token │
                 │ Token   │  │ from IdP      │
                 └─────────┘  └───────────────┘
```

### Error Handling Pattern

```python
class EPMError(Exception):
    """Base exception for EPM CLI errors"""
    def __init__(self, message: str, code: int, suggestion: str = None):
        self.message = message
        self.code = code
        self.suggestion = suggestion
        super().__init__(message)

@click.Command
def artifact_changes(...):
    try:
        result = client.get_artifact_modifications(...)
    except requests.exceptions.ConnectionError:
        raise EPMError(
            "Connection refused: Cannot reach EPM instance",
            code=503,
            suggestion="Check if VPN is connected and hostname is correct"
        )
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise EPMError(
                "Authentication failed: Token expired or invalid",
                code=401,
                suggestion="Run 'epm login <app>' to refresh credentials"
            )
        elif e.response.status_code == 429:
            # Handled by client with retry
            pass
```

## Dependencies

### Required

| Package | Version | Purpose |
|---------|---------|---------|
| click | >= 8.0 | CLI framework |
| requests | >= 2.28 | HTTP client |
| pyyaml | >= 6.0 | Config parsing |
| rich | >= 13.0 | Table output |
| python-dateutil | >= 2.8 | Date parsing |

### Optional

| Package | Version | Purpose |
|---------|---------|---------|
| oci | >= 2.100 | OCI infrastructure commands |
| keyring | >= 23.0 | Local credential storage |

### Existing Code Integration

| Module | Usage |
|--------|-------|
| `credential_manager.py` | OAuth token management, credential backend |
| `config/applications.yaml` | Application configuration, token scopes |
| `extract-artifact-changes.py` | Classification logic reference |

## Open Questions

1. **Caching strategy for large queries?**
   - Option A: Local SQLite cache with TTL
   - Option B: In-memory cache only
   - Recommendation: Start with in-memory, add SQLite if needed

2. **Offline mode?**
   - Allow `epm rule-diff --offline` to compare local files
   - Recommendation: Phase 2, after core commands stable

3. **Parallel requests?**
   - Use `concurrent.futures` for multiple apps
   - Recommendation: Yes, with `--parallel` flag

4. **Plugin system?**
   - Allow custom commands via entry points
   - Recommendation: Phase 2, after API stabilizes