# EPM Audit Automation Project

**Purpose:** Automated extraction and monitoring of audit information across Oracle EPM Cloud applications for Internal Control and SOX compliance.

## Scope

### EPM Applications
| Application | Purpose | Audit Focus |
|-------------|---------|-------------|
| **FCCS** | Financial Consolidation & Close | Consolidation rules, journal entries, period close |
| **PBCS** | Planning & Budgeting | Planning models, data forms, approval workflows |
| **EDM** | Enterprise Data Management | Master data changes, hierarchy updates, approvals |
| **ARCS** | Account Reconciliation | Reconciliation status, transactions, aging |
| **TRCS** | Tax Reporting | Tax provision, compliance reporting |
| **PCM** | Profitability & Cost Management | Allocation rules, profitability models |

### Infrastructure
| Component | Purpose |
|-----------|---------|
| **Data Exchange** | Data integration, load logs, error tracking |
| **OCI Integration** | IAM, audit logs, resource tracking |

## Project Structure

```
epm-audit-automation/
├── docs/
│   ├── audit-points.md          # Complete audit extraction matrix
│   ├── sox-controls.md          # SOX control mapping
│   ├── api-reference.md         # REST API endpoints
│   └── extraction-schedule.md   # Recommended schedule per artifact
├── scripts/
│   ├── extract-fccs-audit.py
│   ├── extract-pbcs-audit.py
│   ├── extract-edm-audit.py
│   ├── extract-arcs-audit.py
│   ├── extract-trcs-audit.py
│   ├── extract-pcm-audit.py
│   ├── extract-oci-logs.py
│   └── consolidate-reports.py
├── config/
│   ├── environments.yaml        # EPM environment configurations
│   ├── credentials.template     # Auth placeholders
│   └── audit-config.yaml        # What to extract, retention, etc.
└── outputs/
    ├── raw/                     # Daily extraction dumps
    ├── processed/               # Normalized/transformed
    └── reports/                 # SOX-ready reports
```

## Quick Start

1. **Configure environments** in `config/environments.yaml`
2. **Set up credentials** (OCI Vault or encrypted local)
3. **Test extraction** for one application
4. **Schedule automation** via cron or OCI Functions

## Compliance Targets

- **SOX 302:** CEO/CFO certification support data
- **SOX 404:** Internal control documentation
- **Change Management:** Who changed what, when, why
- **Access Review:** User provisioning/deprovisioning evidence
- **Data Integrity:** Load validation, reconciliation proof

---
*Last updated: 2026-02-26*
