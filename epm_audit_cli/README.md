# EPM Audit CLI

CLI for Oracle EPM Cloud audit and governance operations that fill gaps in EPM Automate.

## Quick Start

```bash
# Install
cd projects/epm-audit-automation/epm_audit_cli
pip install -e .

# Login
epm login fccs_prod --verify

# Query artifact changes
epm artifact-changes --app fccs_prod --from 2026-03-01 --to 2026-03-27

# List EDM requests
epm edm-requests --app edm_prod --status COMPLETED
```

## Documentation

Full documentation available in `docs/`:

| Document | Description |
|----------|-------------|
| [docs/README.md](docs/README.md) | Complete user guide with installation, configuration, commands |
| [docs/configuration.md](docs/configuration.md) | Configuration file reference |

## Commands

| Command | Description |
|---------|-------------|
| `epm login <app>` | Authenticate to EPM application |
| `epm logout` | Clear cached tokens |
| `epm artifact-changes` | Query artifact modification history |
| `epm edm-requests` | List EDM request history |
| `epm edm-request` | Get EDM request details |
| `epm edm-violations` | List EDM policy violations |
| `epm rules` | List business rules |
| `epm rule` | Get rule definition |
| `epm rule-diff` | Compare rule against baseline |
| `epm oci-instances` | List OCI compute instances |
| `epm oci-storage` | Get OCI storage bucket info |
| `epm oci-network` | Get OCI VCN status |
| `epm iam users` | List OCI IAM users |
| `epm iam groups` | List OCI IAM groups |
| `epm iam memberships` | List user-group memberships |
| `epm iam access-review` | Generate SOX access review |

## Output Formats

All commands support: `table` (default), `json`, `csv`

```bash
epm artifact-changes --app fccs_prod --from 2026-03-01 --output json
epm artifact-changes --app fccs_prod --from 2026-03-01 --output csv > changes.csv
```

## Artifact Classification

| Type | Classification | SOX Relevance |
|------|----------------|----------------|
| Rules, forms, dimensions | MATERIAL | SOX relevant |
| Jobs, periods, snapshots | OPERATIONAL | Not SOX relevant |
| Unknown types | REVIEW_REQUIRED | Manual review |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black epm_audit_cli/
ruff check epm_audit_cli/
```

## License

MIT