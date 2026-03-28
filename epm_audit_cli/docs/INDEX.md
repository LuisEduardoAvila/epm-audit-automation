# EPM Audit CLI Documentation Index

## Getting Started

1. **[README.md](../README.md)** — Quick start guide
2. **[docs/README.md](README.md)** — Complete user guide
3. **[docs/configuration.md](configuration.md)** — Configuration reference

## By Use Case

### SOX Audit Trails

- **[artifact-changes command](README.md#artifact-changes)** — Query configuration modification history
- **[Classification](README.md#classification)** — Understand MATERIAL vs OPERATIONAL changes
- **[SOX Audit Report Example](README.md#sox-audit-trail-report)** — Monthly report script

### Access Reviews (IAM)

- **[iam users command](README.md#list-users)** — List OCI IAM users with filters
- **[iam groups command](README.md#list-groups)** — List OCI IAM groups
- **[iam memberships command](README.md#list-memberships)** — User-group membership mapping
- **[iam access-review command](README.md#sox-access-review)** — Comprehensive SOX access review report
- **[User Filters](README.md#list-users)** — Filter by service-accounts, dormant, privileged, orphan

### EDM Monitoring

- **[edm-requests command](README.md#list-edm-requests)** — Track metadata deployment requests
- **[edm-violations command](README.md#list-edm-policy-violations)** — Monitor policy violations
- **[EDM Monitoring Example](README.md#edm-request-monitoring)** — Failed request alerting

### Business Rule Auditing

- **[rules command](README.md#list-rules)** — List all business rules
- **[rule command](README.md#get-rule-definition)** — Export rule definition
- **[rule-diff command](README.md#compare-rule-against-baseline)** — Detect unauthorized changes
- **[Unauthorized Change Detection Example](README.md#detect-unauthorized-changes)** — Baseline comparison script

### OCI Infrastructure

- **[oci-instances command](README.md#list-compute-instances)** — Monitor compute instances
- **[oci-storage command](README.md#storage-bucket-info)** — Check storage buckets
- **[oci-network command](README.md#network-status)** — Verify network configuration

## By Output Format

- **[Table Output](README.md#table-default)** — Human-readable tables
- **[JSON Output](README.md#json)** — Machine-readable for scripting
- **[CSV Output](README.md#csv)** — Excel-compatible format

## Configuration

- **[Application Configuration](configuration.md#application-configuration)** — Define EPM apps
- **[Authentication Methods](configuration.md#authentication-methods)** — OAuth, Basic, OCI Vault
- **[Environment Variables](configuration.md#environment-variables)** — Credential management
- **[Multi-Environment Setup](configuration.md#multi-environment-setup)** — Dev/Test/Prod

## Development

- **[Architecture](README.md#architecture)** — Package structure
- **[Error Handling](README.md#error-handling)** — Exception hierarchy
- **[Adding Commands](README.md#adding-new-commands)** — Extend the CLI
- **[Tests](README.md#run-tests)** — Run test suite

## Troubleshooting

- **[Common Issues](README.md#common-issues)** — Errors and fixes
- **[Debug Mode](README.md#debug-mode)** — Enable verbose output
- **[Getting Help](README.md#getting-help)** — Command help

## Quick Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `login` | Authenticate | `epm login fccs_prod --verify` |
| `artifact-changes` | SOX audit trail | `epm artifact-changes --app fccs_prod --from 2026-03-01` |
| `edm-requests` | EDM history | `epm edm-requests --app edm_prod --status COMPLETED` |
| `edm-violations` | Policy issues | `epm edm-violations --app edm_prod --severity HIGH` |
| `rules` | List rules | `epm rules --app pbcs_prod --type CALCULATION` |
| `rule-diff` | Compare baseline | `epm rule-diff --app pbcs_prod --id Calc --baseline b.json` |
| `oci-instances` | OCI compute | `epm oci-instances --compartment ocid1...` |
| `iam users` | IAM users | `epm iam users -c ocid1... --filter privileged` |
| `iam groups` | IAM groups | `epm iam groups -c ocid1...` |
| `iam memberships` | User-group map | `epm iam memberships -c ocid1...` |
| `iam access-review` | SOX access review | `epm iam access-review -c ocid1... --output csv` |