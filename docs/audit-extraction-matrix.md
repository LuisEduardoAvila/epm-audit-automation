# EPM Audit Extraction Matrix

*Complete reference of all audit-relevant data points across Oracle EPM Cloud*

---

## 1. FCCS (Financial Consolidation and Close Cloud Service)

### Core Audit Artifacts

| Artifact | API Endpoint | Extraction Method | Frequency | SOX Relevance |
|----------|--------------|-------------------|-----------|---------------|
| **Journal Entries** | `/interop/rest/{version}/applications/{application}/ journals` | REST API | Daily | Critical - All manual/posted entries |
| **Consolidation Rules** | `/aif/rest/{version}/jobs` + rule execution logs | REST API | Weekly | High - Automated calculations |
| **Period Close Status** | `/calendars` + period state | REST API | Daily | Critical - Close timeline evidence |
| **Data Forms Audit** | `/dataforms/{form}/audit` | REST API | Weekly | Medium - Data entry changes |
| **Security/Users** | `/security/users` + `/security/groups` | EPM Automate | Weekly | Critical - Access review |
| **Dimension Changes** | `/dimensions/{dim}/members/audit` | REST API | Daily | High - Chart of accounts changes |
| **Task Manager** | `/tasks` + completion status | REST API | Daily | Medium - Close task evidence |
| **Supplemental Data** | `/supplementaldata` | REST API | Weekly | Medium - Supporting schedules |

### FCCS-Specific Logs
```
Artifact Types:
- Consolidation log (rule execution detail)
- Translation log (currency conversion)
- Intercompany matching status
- Ownership management changes
- Equity pickup calculations
```

---

## 2. PBCS (Planning and Budgeting Cloud Service)

### Core Audit Artifacts

| Artifact | API Endpoint | Extraction Method | Frequency | SOX Relevance |
|----------|--------------|-------------------|-----------|---------------|
| **Data Input Forms** | `/applications/{app}/forms` + history | REST API | Weekly | High - Manual data entry |
| **Planning Approval** | `/approval` + workflow status | REST API | Daily | Critical - Budget sign-off |
| **Business Rules** | `/businessrules` + execution log | REST API | Weekly | Medium - Calculation logic |
| **Smart Lists** | `/smartlists` + changes | REST API | Monthly | Low - Drop-down values |
| **User Variables** | `/uservariables` | REST API | Monthly | Low - User context |
| **Security Filters** | `/securityfilters` | REST API | Weekly | High - Row-level security |
| **Audit Trail** | `/audit` - who changed what cells | REST API | Daily | Critical - Cell-level changes |

### PBCS-Specific Considerations
```
Key Extraction Points:
- Version changes (Working → Final)
- Scenario modifications (Actual → Forecast)
- Plan type structure changes
- Currency rate table updates
- Substitution variable changes
```

---

## 3. EDM (Enterprise Data Management)

### Core Audit Artifacts

| Artifact | API Endpoint | Extraction Method | Frequency | SOX Relevance |
|----------|--------------|-------------------|-----------|---------------|
| **Hierarchy Changes** | `/applications/{app}/views/{view}/requests` | REST API | Daily | Critical - Org structure |
| **Node Changes** | `/nodes/{node}/history` | REST API | Daily | Critical - Account changes |
| **Request History** | `/requests` + approval workflow | REST API | Daily | Critical - Change approval |
| **Policy Violations** | `/policies/violations` | REST API | Weekly | Medium - Governance |
| **User Access** | `/security/access` | REST API | Weekly | High - Access review |
| **Data Chain** | `/chains` + lineage | REST API | Monthly | Medium - Data flow |

### EDM Critical for SOX
```
Must Track:
- Account hierarchy changes (affects FCCS/ARCS)
- Cost center restructures
- Product line additions/changes
- Intercompany partner updates
- Currency/entity mappings
```

---

## 4. ARCS (Account Reconciliation Cloud Service)

### Core Audit Artifacts

| Artifact | API Endpoint | Extraction Method | Frequency | SOX Relevance |
|----------|--------------|-------------------|-----------|---------------|
| **Reconciliation Status** | `/reconciliations` | REST API | Daily | Critical - Close status |
| **Transaction Details** | `/reconciliations/{id}/transactions` | REST API | Daily | High - Supporting detail |
| **Balance Explained** | `/reconciliations/{id}/explained` | REST API | Daily | Critical - Aging analysis |
| **User Comments** | `/reconciliations/{id}/comments` | REST API | Daily | Medium - Justification |
| **Attachment Evidence** | `/reconciliations/{id}/attachments` | REST API | Weekly | Medium - Documentation |
| **Format Changes** | `/formats` + history | REST API | Monthly | Low - Template changes |
| **Security/Profiles** | `/profiles` + assignments | REST API | Weekly | High - Who reconciles what |
| **Compliance Rules** | `/rules` + violations | REST API | Weekly | Medium - Auto-certification |

### ARCS Audit Report Types
```
Standard Reports:
- Reconciliation Compliance (certified/uncertified)
- Age Profile (30/60/90/120+ days)
- Transaction Volume by Preparer
- Auto-Reconciliation Statistics
- Manual Adjustment Tracking
```

---

## 5. TRCS (Tax Reporting Cloud Service)

### Core Audit Artifacts

| Artifact | API Endpoint | Extraction Method | Frequency | SOX Relevance |
|----------|--------------|-------------------|-----------|---------------|
| **Tax Provision** | `/taxprovisions` + calculations | REST API | Per close | Critical - Tax expense |
| **Rate Changes** | `/taxrates` + effective dates | REST API | Quarterly | High - Rate validation |
| **Jurisdiction Tables** | `/jurisdictions` | REST API | Quarterly | Medium - Entity mapping |
| **Adjustment Entries** | `/adjustments` | REST API | Per close | Critical - Manual entries |
| **Return to Accrual** | `/rta` differences | REST API | Quarterly | High - Reconciliation |
| **Deferred Tax** | `/deferredtax` rollforward | REST API | Per close | Critical - DTA/DTL |

---

## 6. PCM (Profitability and Cost Management)

### Core Audit Artifacts

| Artifact | API Endpoint | Extraction Method | Frequency | SOX Relevance |
|----------|--------------|-------------------|-----------|---------------|
| **Allocation Rules** | `/rules` + execution history | REST API | Weekly | High - Cost allocation |
| **Model Changes** | `/models` + version history | REST API | Monthly | Medium - Structure changes |
| **Traceability** | `/trace` reports | REST API | Per allocation | High - Audit trail |
| **Driver Data** | `/drivers` + updates | REST API | Weekly | Medium - Allocation basis |
| **Stage Balances** | `/stages/{stage}/balances` | REST API | Per allocation | High - Inter-stage proof |

---

## 7. Data Exchange (EPM Integration)

### Core Audit Artifacts

| Artifact | Location | Extraction Method | Frequency | SOX Relevance |
|----------|----------|-------------------|-----------|---------------|
| **Data Load Rules** | `/dataexchange/rules` | REST API | Weekly | Medium - Load logic |
| **Execution Logs** | `/dataexchange/executions` | REST API | Daily | Critical - Load success/fail |
| **Error Reports** | `/dataexchange/errors` | REST API | Daily | High - Data integrity |
| **Mapping Tables** | `/dataexchange/mappings` | REST API | Weekly | Medium - Data transformation |
| **Source System Logs** | Audit table | SQL/EPM | Daily | High - Source to target |
| **File Transfer Logs** | Inbox/Outbox | File scan | Daily | Medium - File-based loads |

### Data Exchange Critical Checks
```
Must Monitor:
- Failed loads (immediate alert)
- Record count variances
- Mapping errors
- Transformation failures
- Duplicate record detection
```

---

## 8. OCI Integration (Oracle Cloud Infrastructure)

### Core Audit Artifacts

| Artifact | OCI Service | Extraction Method | Frequency | SOX Relevance |
|----------|-------------|-------------------|-----------|---------------|
| **Audit Logs** | Audit Service | OCI CLI/API | Real-time | Critical - All API calls |
| **IAM Changes** | Identity Service | OCI CLI | Daily | Critical - User/role changes |
| **Sign-In Events** | IAM Audit | OCI CLI | Daily | Critical - Access evidence |
| **Compartment Changes** | IAM/Compartments | OCI CLI | Weekly | Medium - Resource org |
| **Network Security Groups** | Networking | OCI CLI | Weekly | High - Firewall rules |
| **Database Audit** | Autonomous DB | SQL Queries | Daily | Critical - Direct DB access |
| **Object Storage Access** | Object Storage | OCI CLI | Daily | Medium - File access |
| **Function Invocations** | Functions | OCI CLI | Daily | Medium - Automation logs |

### OCI Audit Log Critical Events
```
Must Capture:
- epminstance:create, epminstance:delete
- user:create, user:delete, user:update
- group:add-user, group:remove-user
- policy:create, policy:update
- compartment:create, compartment:delete
- apikey:create, apikey:delete
- authtoken:create, authtoken:delete
```

---

## Extraction Summary by Frequency

### Daily (Critical for SOX)
1. FCCS: Journal entries, period close status
2. PBCS: Approval workflows, audit trail
3. EDM: Hierarchy/requests, node history
4. ARCS: Reconciliation status, transactions
5. Data Exchange: Execution logs, errors
6. OCI: IAM changes, audit logs

### Weekly (Medium Priority)
1. FCCS: Users/groups, dimension changes
2. PBCS: Forms, security filters
3. EDM: Policy violations
4. ARCS: Security profiles, attachments
5. TRCS: Rate tables (if quarterly close)
6. PCM: Allocation rules, driver data
7. OCI: Compartment changes

### Monthly/Quarterly (Lower Priority)
- Smart Lists (PBCS)
- Model changes (PCM)
- Jurisdiction tables (TRCS)
- Compliance rule updates

---

## API Authentication Methods

| Method | Applications | Notes |
|--------|--------------|-------|
| **Basic Auth** | FCCS, PBCS, EDM, ARCS | Username/password or SSO |
| **OAuth 2.0** | All EPM Cloud | Recommended for automation |
| **OCI API Key** | OCI Services | PEM key + fingerprint |
| **Instance Principal** | OCI Services | For OCI Functions/Compute |

---

## Recommended Data Retention

| Data Type | SOX Requirement | Recommendation |
|-----------|-----------------|----------------|
| Journal Entries | 7 years | 7+ years |
| User Access Logs | 7 years | 7+ years |
| Period Close Evidence | 7 years | Permanent |
| Reconciliation Data | 7 years | 7+ years |
| OCI Audit Logs | 1 year | 2+ years (store in Object Storage) |
| System Config Changes | 7 years | 7+ years |

---

## Next Steps

1. **Review this matrix** and add organization-specific customizations
2. **Set up EPM Automate** or REST API access for each environment
3. **Configure OCI IAM** for audit log access
4. **Create extraction scripts** (see `/scripts/` directory)
5. **Schedule automation** (recommend OCI Functions for cloud-native)

---

*Document Version: 1.0*
*Last Updated: 2026-02-26*
*Owner: EPM Architecture Team*
