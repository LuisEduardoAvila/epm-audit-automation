# EPM Audit CLI Documentation

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Authentication](#authentication)
5. [Commands](#commands)
6. [Output Formats](#output-formats)
7. [Examples](#examples)
8. [Architecture](#architecture)
9. [Development](#development)

---

## Overview

EPM Audit CLI is a command-line tool for Oracle EPM Cloud audit and governance operations. It fills gaps in Oracle's EPM Automate CLI by providing:

- **Artifact Change Tracking** — Query configuration modification history for SOX audit trails
- **EDM Request History** — Retrieve metadata deployment records and policy violations
- **Business Rule Inspection** — Extract and diff rule logic against baselines
- **OCI Infrastructure Monitoring** — Track compute, storage, and networking resources

### Why This CLI?

Oracle EPM Automate covers operational tasks well (jobs, snapshots, imports), but lacks audit-specific commands:

| Gap | EPM Audit CLI Command | SOX Relevance |
|-----|----------------------|---------------|
| Artifact modification history | `epm artifact-changes` | Critical |
| EDM request tracking | `epm edm-requests` | High |
| EDM policy violations | `epm edm-violations` | High |
| Business rule diffs | `epm rule-diff` | Medium |
| OCI infrastructure | `epm oci-instances` | Medium |

---

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager
- Oracle EPM Cloud account with API access
- OCI CLI configured (optional, for OCI commands)

### Install from Source

```bash
# Clone or navigate to project
cd /path/to/epm-audit-automation

# Navigate to CLI package
cd epm_audit_cli

# Install in development mode
pip install -e .
```

### Verify Installation

```bash
epm --version
# Output: epm-audit-cli 0.1.0

epm --help
# Shows available commands
```

### Dependencies

The package installs these dependencies automatically:

| Package | Purpose |
|---------|---------|
| click>=8.0.0 | CLI framework |
| requests>=2.28.0 | HTTP client |
| pyyaml>=6.0.0 | Configuration files |
| rich>=13.0.0 | Console output formatting |
| python-dateutil>=2.8.0 | Date parsing |

**Optional:**

| Package | Purpose |
|---------|---------|
| oci | OCI SDK for infrastructure commands |

```bash
# Install with OCI support
pip install -e ".[oci]"
```

---

## Configuration

### Application Configuration

Create `config/applications.yaml` in your project directory:

```yaml
# EPM Application Configuration
# See docs/configuration.md for full reference

applications:
  # ============================================
  # PRODUCTION ENVIRONMENT
  # ============================================
  
  fccs_prod:
    name: "FCCS Production"
    type: "FCCS"
    environment: "production"
    
    connection:
      base_url: "https://company-fccs.epm.us-phoenix-1.oraclecloud.com"
      region: "us-phoenix-1"
      tenant: "company"
      service: "fccs"
    
    authentication:
      method: "oauth"
      client_id: "${FCCS_CLIENT_ID}"
      scope: "epm.api"

  # ============================================
  # NON-PRODUCTION ENVIRONMENT
  # ============================================
  
  fccs_dev:
    name: "FCCS Development"
    type: "FCCS"
    environment: "development"
    
    connection:
      base_url: "https://company-fccs-dev.epm.us-phoenix-1.oraclecloud.com"
      region: "us-phoenix-1"
      tenant: "company"
      service: "fccs"
    
    authentication:
      method: "oauth"
      client_id: "${FCCS_DEV_CLIENT_ID}"

  # ============================================
  # PLANNING APPLICATION
  # ============================================
  
  pbcs_prod:
    name: "Planning Production"
    type: "PBCS"
    environment: "production"
    
    connection:
      base_url: "https://company-pbcs.epm.us-phoenix-1.oraclecloud.com"
      region: "us-phoenix-1"
      tenant: "company"
      service: "pbcs"

  # ============================================
  # ENTERPRISE DATA MANAGEMENT
  # ============================================
  
  edm_prod:
    name: "EDM Production"
    type: "EDM"
    environment: "production"
    
    connection:
      base_url: "https://company-edm.epm.us-phoenix-1.oraclecloud.com"
      region: "us-phoenix-1"
```

### Environment Variables

Set credentials via environment variables (recommended for security):

```bash
# OAuth credentials
export FCCS_CLIENT_ID="your-client-id"
export FCCS_CLIENT_SECRET="your-client-secret"

# Or use OCI Vault (see docs/authentication.md)
```

### Configuration File Location

The CLI searches for configuration in this order:

1. `--config` flag: `epm login fccs_prod --config /path/to/applications.yaml`
2. Environment variable: `EPM_CONFIG_PATH`
3. Current directory: `./config/applications.yaml`
4. Home directory: `~/.epm-audit/config/applications.yaml`

---

## Authentication

### Login Flow

```bash
# Basic login
epm login fccs_prod

# Login with connection verification
epm login fccs_prod --verify

# Login with specific backend
epm login fccs_prod --backend oci-vault
```

### Token Management

The CLI integrates with the existing credential manager:

- **Token Caching**: Tokens cached in `~/.epm-audit/tokens/`
- **Auto-Refresh**: Tokens refreshed before expiry
- **Multiple Apps**: Separate tokens per application

### Logout

```bash
# Logout from current session
epm logout

# Logout from all applications
epm logout --all
```

---

## Commands

### Artifact Changes

Query artifact modification history for SOX audit trails.

```bash
# Basic usage
epm artifact-changes --app fccs_prod --from 2026-03-01 --to 2026-03-27

# Filter by artifact type
epm artifact-changes --app fccs_prod --from 2026-03-01 --type CONSOLIDATION_RULE
epm artifact-changes --app fccs_prod --from 2026-03-01 --type DATA_FORM
epm artifact-changes --app fccs_prod --from 2026-03-01 --type DIMENSION

# Filter by user
epm artifact-changes --app fccs_prod --from 2026-03-01 --modified-by john.smith

# Exclude service accounts (pattern matching)
epm artifact-changes --app fccs_prod --from 2026-03-01 --modified-by-exclude "svc_*"

# Multiple artifact types
epm artifact-changes --app fccs_prod --from 2026-03-01 --type CONSOLIDATION_RULE --type DATA_FORM

# Limit results
epm artifact-changes --app fccs_prod --from 2026-03-01 --limit 100

# Output formats
epm artifact-changes --app fccs_prod --from 2026-03-01 --output json
epm artifact-changes --app fccs_prod --from 2026-03-01 --output csv > changes.csv
```

#### Classification

Changes are automatically classified:

| Classification | Types | SOX Relevance |
|----------------|-------|----------------|
| **MATERIAL** | Rules, forms, dimensions, smart lists | SOX relevant |
| **OPERATIONAL** | Jobs, periods, snapshots, backups | Not SOX relevant |
| **REVIEW_REQUIRED** | Unknown types | Manual review |

### EDM Commands

#### List EDM Requests

```bash
# All requests
epm edm-requests --app edm_prod

# Filter by status
epm edm-requests --app edm_prod --status COMPLETED
epm edm-requests --app edm_prod --status FAILED
epm edm-requests --app edm_prod --status PENDING

# Date range
epm edm-requests --app edm_prod --from 2026-03-01 --to 2026-03-27

# Limit results
epm edm-requests --app edm_prod --limit 50

# JSON output
epm edm-requests --app edm_prod --output json | jq '.[] | select(.status == "FAILED")'
```

#### Get EDM Request Details

```bash
epm edm-request --app edm_prod --id REQ-2026-0226-001
```

#### List EDM Policy Violations

```bash
# All violations
epm edm-violations --app edm_prod

# Filter by severity
epm edm-violations --app edm_prod --severity HIGH
epm edm-violations --app edm_prod --severity CRITICAL

# Date range
epm edm-violations --app edm_prod --from 2026-03-01 --to 2026-03-27
```

### Business Rules

#### List Rules

```bash
# All rules
epm rules --app pbcs_prod

# Filter by type
epm rules --app pbcs_prod --type CALCULATION
epm rules --app pbcs_prod --type ALLOCATION
epm rules --app pbcs_prod --type VALIDATION
```

#### Get Rule Definition

```bash
# Display to console
epm rule --app pbcs_prod --id Calc_Headcount

# Export to file
epm rule --app pbcs_prod --id Calc_Headcount --output-file calc_headcount.json
```

#### Compare Rule Against Baseline

```bash
# Compare current vs baseline snapshot
epm rule-diff --app pbcs_prod --id Calc_Headcount --baseline snapshots/baseline.json

# Useful for detecting unauthorized changes
epm rule-diff --app pbcs_prod --id Calc_Revenue --baseline baselines/q1_baseline.json
```

### OCI Infrastructure

> **Note:** Requires `oci` package. Install with `pip install oci` or `pip install -e ".[oci]"`.

#### List Compute Instances

```bash
# All instances in compartment
epm oci-instances --compartment ocid1.compartment.oc1..xxx

# Filter by state
epm oci-instances --compartment ocid1.compartment.oc1..xxx --status RUNNING
epm oci-instances --compartment ocid1.compartment.oc1..xxx --status STOPPED

# Filter by tag
epm oci-instances --compartment ocid1.compartment.oc1..xxx --filter-tag epm=true
epm oci-instances --compartment ocid1.compartment.oc1..xxx --filter-tag environment=production
```

#### Storage Bucket Info

```bash
epm oci-storage --bucket epm-backups
epm oci-storage --bucket fccs-snapshots --output json
```

#### Network Status

```bash
# Get VCN status
epm oci-network --vcn ocid1.vcn.oc1.phx.xxx

# With compartment filter
epm oci-network --vcn ocid1.vcn.oc1.phx.xxx --compartment ocid1.compartment.oc1..xxx
```

### IAM / IDCS Commands

> **Note:** Requires `oci` package. Install with `pip install oci` or `pip install -e ".[oci]"`.

Query OCI IAM for users, groups, and memberships for SOX access reviews.

#### List Users

```bash
# All users in compartment
epm iam users --compartment ocid1.compartment.oc1..xxx

# Filter by type
epm iam users -c ocid1.compartment.oc1..xxx --filter service-accounts
epm iam users -c ocid1.compartment.oc1..xxx --filter dormant
epm iam users -c ocid1.compartment.oc1..xxx --filter privileged
epm iam users -c ocid1.compartment.oc1..xxx --filter orphan

# Export to CSV
epm iam users -c ocid1.compartment.oc1..xxx --output csv --file users.csv
```

#### List Groups

```bash
# All groups in compartment
epm iam groups --compartment ocid1.compartment.oc1..xxx

# Filter privileged groups only
epm iam groups -c ocid1.compartment.oc1..xxx --filter privileged

# JSON output
epm iam groups -c ocid1.compartment.oc1..xxx --output json
```

#### List Memberships

```bash
# All user-group memberships
epm iam memberships --compartment ocid1.compartment.oc1..xxx

# Filter by group
epm iam memberships -c ocid1.compartment.oc1..xxx --group Administrators

# CSV export
epm iam memberships -c ocid1.compartment.oc1..xxx --output csv --file memberships.csv
```

#### SOX Access Review

Generate comprehensive access review report:

```bash
# Full access review
epm iam access-review --compartment ocid1.compartment.oc1..xxx

# Export to CSV for auditors
epm iam access-review -c ocid1.compartment.oc1..xxx --output csv --file access-review.csv

# Adjust dormant threshold
epm iam access-review -c ocid1.compartment.oc1..xxx --dormant-days 60
```

**Access Review includes:**
- Total users (human + service accounts)
- Privileged users (admin group members)
- Dormant accounts (no login >90 days)
- Orphan accounts (no group memberships)
- Group assignments
- SoD (Segregation of Duties) violations
- Security flags and recommendations

---

## Output Formats

All commands support three output formats:

### Table (Default)

Human-readable format with aligned columns.

```bash
epm artifact-changes --app fccs_prod --from 2026-03-01
```

Output:
```
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Date           ┃ Type               ┃ Name             ┃ Modified By  ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ 2026-03-27     │ CONSOLIDATION_RULE │ Calc_Headcount   │ john.smith   │
│ 2026-03-26     │ DATA_FORM          │ Input_Sales      │ admin        │
│ 2026-03-25     │ DIMENSION          │ Entity           │ svc_migration│
└────────────────┴────────────────────┴──────────────────┴──────────────┘
```

### JSON

Machine-readable format for scripting.

```bash
epm artifact-changes --app fccs_prod --from 2026-03-01 --output json
```

Output:
```json
[
  {
    "date": "2026-03-27",
    "artifactType": "CONSOLIDATION_RULE",
    "artifactName": "Calc_Headcount",
    "modifiedBy": "john.smith",
    "classification": "MATERIAL"
  }
]
```

Pipe to `jq` for filtering:
```bash
epm artifact-changes --app fccs_prod --from 2026-03-01 --output json | \
  jq '.[] | select(.classification == "MATERIAL")'
```

### CSV

Excel-compatible format.

```bash
epm artifact-changes --app fccs_prod --from 2026-03-01 --output csv > changes.csv
```

Output:
```csv
date,artifactType,artifactName,modifiedBy,classification
2026-03-27,CONSOLIDATION_RULE,Calc_Headcount,john.smith,MATERIAL
2026-03-26,DATA_FORM,Input_Sales,admin,MATERIAL
2026-03-25,DIMENSION,Entity,svc_migration,MATERIAL
```

---

## Examples

### SOX Audit Trail Report

Generate monthly artifact change report:

```bash
#!/bin/bash
# monthly-audit-report.sh

APP="fccs_prod"
FROM="2026-03-01"
TO="2026-03-31"

echo "=== SOX Audit Trail Report ===" 
echo "Period: $FROM to $TO"
echo ""

# Get material changes only
echo "Material Configuration Changes:"
epm artifact-changes --app $APP --from $FROM --to $TO --output json | \
  jq '.[] | select(.classification == "MATERIAL")' | \
  jq -r '"- \(.date): \(.artifactType) \(.artifactName) by \(.modifiedBy)"'

echo ""

# Summary statistics
echo "Summary:"
epm artifact-changes --app $APP --from $FROM --to $TO --output json | \
  jq '{
    total: length,
    material: [.[] | select(.classification == "MATERIAL")] | length,
    operational: [.[] | select(.classification == "OPERATIONAL")] | length,
    review_required: [.[] | select(.classification == "REVIEW_REQUIRED")] | length
  }'
```

### Detect Unauthorized Changes

Compare business rules against approved baseline:

```bash
#!/bin/bash
# detect-unauthorized-changes.sh

APP="pbcs_prod"
BASELINE="approved_baselines/q1_2026.json"

# Get list of critical rules
RULES=$(epm rules --app $APP --output json | jq -r '.[].name')

echo "Checking rules against baseline..."

for RULE in $RULES; do
  echo -n "Checking $RULE... "
  
  # Diff against baseline
  DIFF=$(epm rule-diff --app $APP --id "$RULE" --baseline "$BASELINE" 2>&1)
  
  if echo "$DIFF" | grep -q "No differences found"; then
    echo "✓ OK"
  else
    echo "⚠ CHANGED"
    echo "$DIFF" >> changes_detected.log
  fi
done
```

### EDM Request Monitoring

Monitor failed EDM requests:

```bash
#!/bin/bash
# edm-monitor.sh

APP="edm_prod"

# Get failed requests in last 7 days
FAILED=$(epm edm-requests --app $APP --status FAILED --from $(date -d '-7 days' +%Y-%m-%d) --output json)

if [ "$(echo "$FAILED" | jq 'length')" -gt 0 ]; then
  echo "⚠ Failed EDM requests detected:"
  echo "$FAILED" | jq -r '.[] | "- \(.requestId): \(.errorMessage)"'
  
  # Send alert (example with mail)
  # echo "$FAILED" | mail -s "EDM Failures Alert" admin@company.com
fi
```

---

## Architecture

### Package Structure

```
epm_audit_cli/
├── pyproject.toml           # Package metadata, dependencies
├── README.md                # Quick start guide
└── epm_audit_cli/
    ├── __init__.py          # Package exports
    ├── cli.py               # Click CLI entry point
    ├── exceptions.py         # EPMError hierarchy
    │
    ├── config/
    │   ├── __init__.py
    │   └── loader.py        # ConfigLoader (YAML parsing)
    │
    ├── clients/
    │   ├── __init__.py
    │   ├── base.py          # BaseAPIClient (retry, pagination)
    │   └── iam.py           # IAMClient (OCI Identity)
    │
    ├── output/
    │   ├── __init__.py      # format_output() helper
    │   ├── table.py         # Rich table formatter
    │   ├── json_fmt.py      # JSON formatter
    │   └── csv_fmt.py       # CSV formatter
    │
    └── commands/
        ├── __init__.py      # Command exports
        ├── login.py         # Authentication
        ├── logout.py        # Token cleanup
        ├── artifact.py      # artifact-changes
        ├── edm.py           # edm-requests, edm-violations
        ├── rules.py         # rules, rule, rule-diff
        ├── oci.py           # oci-instances, oci-storage, oci-network
        └── iam.py           # iam-users, iam-groups, iam-memberships, iam-access-review
```

### Design Principles

1. **Single Responsibility**: Each command module handles one domain
2. **Dependency Injection**: Config and clients passed via Click context
3. **Graceful Degradation**: OCI commands work without `oci` package (clear error)
4. **Consistent Output**: All commands use same formatter pattern
5. **Helpful Errors**: `EPMError` includes suggestion for resolution

### Error Handling

```python
# exceptions.py hierarchy
EPMError (base)
├── EPMConnectionError    # Network issues
├── EPMAuthenticationError # Auth failures
├── EPMValidationError    # Bad input
├── EPMRateLimitError     # Throttling
├── EPMNotFoundError      # 404 errors
└── EPMConfigurationError # Config issues
```

Each exception includes:
- `message`: Clear error description
- `code`: HTTP status or error code
- `suggestion`: How to fix it

Example:
```python
raise EPMAuthenticationError(
    "Authentication failed: Token expired",
    suggestion="Run 'epm login fccs_prod' to refresh credentials"
)
```

---

## Development

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd epm-audit-automation

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=epm_audit_cli

# Run specific test
pytest tests/test_artifact.py -v
```

### Code Style

```bash
# Format code
black epm_audit_cli/

# Lint
ruff check epm_audit_cli/

# Type check
mypy epm_audit_cli/
```

### Adding New Commands

1. Create command module in `commands/`
2. Implement command function with Click decorators
3. Export in `commands/__init__.py`
4. Register in `cli.py`
5. Add tests in `tests/`

Example:

```python
# commands/mycommand.py
import click
from rich.console import Console

console = Console()

@click.command()
@click.option("--app", required=True, help="Application ID")
@click.pass_context
def mycommand(ctx: click.Context, app: str) -> None:
    """My command description."""
    console.print(f"[cyan]Running mycommand for {app}...[/cyan]")
    # Implementation
```

```python
# cli.py - add to imports
from epm_audit_cli.commands.mycommand import mycommand

# Add to group
@cli.group()
def mygroup():
    """My group of commands."""
    pass

@mygroup.command()
def mycommand():
    """My command."""
    pass
```

---

## Troubleshooting

### Common Issues

#### "Application 'xxx' not found in configuration"

**Cause:** Application ID doesn't match config file.

**Fix:** Check `config/applications.yaml` for correct app IDs:
```bash
epm login  # Lists available applications
```

#### "Not authenticated to xxx"

**Cause:** Token not cached or expired.

**Fix:** Run login first:
```bash
epm login fccs_prod --verify
```

#### "Connection failed to https://..."

**Cause:** Network issue, wrong URL, or VPN not connected.

**Fix:**
1. Check VPN connection
2. Verify URL in `config/applications.yaml`
3. Try `--verify` flag on login

#### "OCI SDK not installed"

**Cause:** OCI commands require `oci` package.

**Fix:**
```bash
pip install oci
# Or
pip install -e ".[oci]"
```

#### "Rate limit exceeded"

**Cause:** Too many API requests.

**Fix:**
- CLI auto-retries with backoff
- Use `--limit` to reduce results
- Wait before retrying

### Debug Mode

Enable verbose output:

```bash
# Set log level
export EPM_LOG_LEVEL=DEBUG

# Run command
epm artifact-changes --app fccs_prod --from 2026-03-01
```

### Getting Help

```bash
# General help
epm --help

# Command help
epm artifact-changes --help

# Version info
epm --version
```

---

## License

MIT License. See LICENSE file for details.