# EPM Artifact Audit Extraction Matrix

*Application-level artifact changes, mappings, and metadata modifications*

---

## Artifact Modification Report

The built-in EPM report. We automate its extraction and enhance it.

### What the Standard Report Contains

| Field | Purpose | SOX Relevance |
|-------|---------|---------------|
| Artifact Name | What changed | Identify the object |
| Artifact Type | Category (Rule, Form, etc.) | Classification |
| Application | Which EPM app | Scope |
| Modified By | Who changed it | Accountability |
| Modified Date | When it changed | Timeline |
| Change Summary | What changed | Documentation |

### What We Add

| Additional Field | Source | Value |
|-----------------|--------|-------|
| Full Before/After | Artifact Version API | Complete diff |
| Approver | Workflow/Comments | Who approved |
| Impact Analysis | Dependency scan | What else affected |
| Test Results | Execution logs | Did it work |
| SOX Classification | Materiality rules | Critical/Standard |

---

## Application-Specific Artifacts

### FCCS Artifacts

| Artifact | API Endpoint | Change Tracking Method | Extract What |
|----------|-------------|----------------------|--------------|
| **Consolidation Rules** | `/calculations` | Version + Date | Formula changes, member scope |
| **Consolidation Rulesets** | `/rulesets` | Full export | Execution order, dependencies |
| **Data Forms** | `/dataforms` | Metadata + Definition | Layout, rows, columns, formulas |
| **Journal Templates** | `/journaltemplates` | Version history | Template structure, defaults |
| **Dimensions** | `/dimensions/{dim}` | Deployment logs | Member adds/moves/deletes |
| **Attribute Definitions** | `/attributes` | Metadata | Custom attributes |
| **Smart Lists** | `/smartlists` | Full export | Values, mappings |
| **Exchange Rate Tables** | `/rates` | Historical snapshots | Rates by date, currency pairs |
| **Supplemental Data Forms** | `/supplementaldata` | Form metadata | Schedules, layouts |
| **Task Lists/Managers** | `/tasks` | Workflow changes | Steps, assignments |

**FCCS Daily Extraction Priority:**
1. Consolidation Rules (if rule execution changed)
2. Dimension Changes (after import/deploy)
3. Journal Templates (if manual JEs used)
4. Data Forms (weekly unless flagged)
5. Exchange Rates (only if rates changed)

---

### PBCS Artifacts

| Artifact | API Endpoint | Change Tracking Method | Extract What |
|----------|-------------|----------------------|--------------|
| **Data Forms (Grids)** | `/applications/{app}/forms` | Full definition export | Layout, POV, member formulas |
| **Composite Forms** | `/compositeforms` | Definition | Multi-page forms |
| **Business Rules (Cale Scripts)** | `/businessrules` | Script content | Calculation logic, member loops |
| **Business Rule Sets** | `/rulesets` | Execution order | Rule sequence, dependencies |
| **Approval Unit Hierarchies** | `/approvals/dimensions` | Hierarchy snapshot | Who approves what |
| **Planning Unit Promotions** | `/approvals/promotions` | Workflow log | Approval history |
| **Task Lists** | `/tasklists` | Structure | Close/prepare tasks |
| **Substitution Variables** | `/substitutionvariables` | Value history | Global variables |
| **User Variables** | `/uservariariables` | User settings | Context assignments |
| **Smart Lists** | `/smartlists` | Values | Drop-down options |
| **Currency Rates** | `/exchangerates` | Rate tables | Multi-currency conversions |
| **Validations** | `/validations` | Rules | Data entry validations |
| **Essbase Outlines** | (via export) | Outline files | BSO dimension structures |

**PBCS Daily Extraction Priority:**
1. Approval Unit Changes (who approves what)
2. Business Rules (if changed)
3. Forms (weekly unless flagged)
4. Task Lists (when modified)
5. Planning Unit Promotions (during close)

---

### EDM Artifacts

**EDM is THE source for all metadata changes.**

| Artifact | API Endpoint | Change Tracking Method | Extract What |
|----------|-------------|----------------------|--------------|
| **Requests (All)** | `/requests` | Full request log | Who, what, when, approval |
| **Request Items** | `/requests/{id}/items` | Line-by-line | Each change detail |
| **Views** | `/views` | Version snapshots | Hierarchy definitions |
| **View Versions** | `/views/{id}/versions` | Point-in-time | Complete snapshots |
| **Nodes** | `/nodes/{id}/properties` | Property changes | Attributes per node |
| **Node Relationships** | `/nodes/{id}/ancestors` | Structure changes | Parent/child moves |
| **Mappings** | `/mappings` | Rule definitions | Cross-system mappings |
| **Policy Violations** | `/policies/violations` | Log entries | Governance breaks |
| **Import Jobs** | `/imports` | Batch jobs | Bulk load history |
| **Export Jobs** | `/exports` | Batch jobs | Extract history |

**EDM Request = Complete Audit Trail**

```json
{
  "request_id": "REQ-2026-0226-001",
  "submitter": "metadata.admin@company.com",
  "submitted_date": "2026-02-26T09:00:00Z",
  "approved_by": "data.steward@company.com",
  "approved_date": "2026-02-26T11:30:00Z",
  "status": "COMPLETED",
  "change_type": "HIERARCHY_UPDATE",
  "items": [
    {
      "item_id": 1,
      "action": "MOVE",
      "node_name": "100_NewEntity",
      "from_parent": "200_ParentA",
      "to_parent": "300_ParentB",
      "properties": {
        "Description": "New acquisition - Q1",
        "Currency": "USD",
        "DataStorage": "Store"
      }
    }
  ],
  "impacted_applications": ["FCCS", "PBCS", "ARCS"],
  "downstream_deployments": [
    {
      "app": "FCCS",
      "deployment_id": "DEP-001",
      "status": "SUCCESS",
      "timestamp": "2026-02-26T12:00:00Z"
    }
  ]
}
```

**EDM Real-Time Extraction:**
- ALL requests (approved, rejected, pending)
- Policy violations (immediate alert)
- Failed deployments (immediate alert)
- Orphaned nodes (weekly scan)

---

### Data Exchange Artifacts

**Critical for Data Integrity Audit Trail**

| Artifact | API/Export | Change Tracking | Extract What |
|----------|-----------|-----------------|--------------|
| **Data Load Rules** | `/loadrules` | Definition export | Source-to-target mappings |
| **Import Formats** | `/importformats` | Format spec | File layouts, delimiters |
| **Export Formats** | `/exportformats` | Format spec | Output specifications |
| **Execution History** | `/executions` | Run logs | Success/failure/error |
| **Error Reports** | `/executions/{id}/errors` | Error detail | Failed records |
| **Mapping Documentation** | `/loadrules/{id}/mappings` | Transformation logic | Column→Member rules |
| **Period Mappings** | `/periodmappings` | Date conversions | Financial periods |
| **Category Mappings** | `/categorymappings` | Scenario mapping | Actual/Budget/Forecast |
| **Validation Rules** | `/validations` | Data checks | Required fields, ranges |
| **Drill-Through Definitions** | `/drillthroughs` | Configurations | Source system links |

**Data Exchange Load Audit Trail:**

```json
{
  "execution_id": "LD-2026-0226-001",
  "load_rule_name": "GL_to_FCCS_Journal",
  "executed_by": "system",
  "start_time": "2026-02-26T02:00:00Z",
  "end_time": "2026-02-26T02:15:23Z",
  "status": "SUCCESS",
  "source_system": "Oracle_GL",
  "target_application": "FCCS",
  "source_records": 15420,
  "target_records": 15420,
  "rejected_records": 0,
  "validation_failures": 0,
  "mapping_version": "v2.3",
  "mapping_changes": null,
  "transf_summations_applied": [
    "CurrencyConversion: USD→EUR",
    "SignFlipped: Revenue accounts"
  ],
  "data_integrity_checks": {
    "source_total": 12450000.00,
    "target_total": 12450000.00,
    "variance": 0.00,
    "hash_match": true
  }
}
```

**Data Exchange Critical Monitoring:**
- Failed loads (immediate alert)
- Record count mismatches (alert)
- Mapping version changes (track)
- New rejection patterns (analyze)
- Execution time trending (performance)

---

### ARCS Artifacts

| Artifact | API/Export | Change Tracking | Extract What |
|----------|-----------|-----------------|--------------|
| **Reconciliation Formats** | `/formats` | Format definition | Layout, formatting rules |
| **Profiles** | `/profiles` | Assignments | Who reconciles what |
| **Transaction Matching Rules** | `/matchingrules` | Matching logic | Auto-match criteria |
| **Compliance Rules** | `/compliancerules` | Automation rules | Auto-certification |
| **Formats (History)** | `/formats/history` | Versioning | Format changes over time |
| **Currency Rates** | `/currencypairs` | Exchange rates | Multi-currency configs |

---

### PCM Artifacts

| Artifact | API/Export | Change Tracking | Extract What |
|----------|-----------|-----------------|--------------|
| **Stages** | `/stages` | Flow definitions | Model structure |
| **Stage Balances** | `/stages/{id}/balances` | Calc snapshots | Allocation state |
| **Assignment Rules** | `/assignments` | Rule definitions | Source→Target rules |
| **Driver Definitions** | `/drivers` | Driver basis | Allocation factors |
| **Traceability** | `/trace` | Audit trail | Source to final cost |
| **Rule Executions** | `/executions` | Run logs | Allocation results |

---

## Mapping Change Documentation

### Data Exchange Mapping Export

**Standard Export:**
```
Mapping Name: GL_JeToFCCS_Journal
Source: GL.JE_LINES
Target: FCCS.Journal
Version: 3.2
Status: Active

COLUMN MAPPINGS:
┌─────────────────────────┬────────────────────────┬─────────────┐
│ Source Column           │ Target Member/Property │ Transform   │
├─────────────────────────┼────────────────────────┼─────────────┤
│ je_batch_name           │ BatchName              │ None        │
│ je_header_name          │ JournalName            │ None        │
│ je_line_num             │ LineNumber             │ None        │
│ code_combination_id     │ Account (via lookup)   │ Lookup      │
│ accounted_dr            │ Debit                  │ If > 0      │
│ accounted_cr            │ Credit                 │ If > 0      │
│ currency_code           │ Currency               │ None        │
│ entered_dr              │ EnteredDebit           │ None        │
│ entered_cr              │ EnteredCredit          │ None        │
│ accounting_date         │ Period (via mapping)   │ Date→Period │
│ je_category             │ Scenario (via lookup)  │ Lookup      │
│ segment1 (Entity)       │ Entity                 │ Direct      │
│ segment2 (Cost Center)  │ Custom2                │ Direct      │
│ segment3 (Product)      │ Product                │ Direct      │
│ description             │ LineItemDescription    │ None        │
└─────────────────────────┴────────────────────────┴─────────────┘

LOOKUP TABLES:
  Account Mapping: GL_ACC_TO_FCCS_ACC
  Scenario Mapping: GL_CAT_TO_SCENARIO
  Period Mapping: GL_DATE_TO_PERIOD

VALIDATION RULES:
  ✓ Required fields: Batch, Journal, Account, Period
  ✓ Debit/Credit must sum to zero
  ✓ Account must exist in FCCS
  ✓ Entity must be active/valid

TRANSFORMATIONS APPLIED:
  1. Currency conversion (if different from functional)
  2. Sign flip for specific account types
  3. Date to Period conversion
  4. Account hierarchy rollup validation
```

---

## Artifact Change Detection

### How We Track Changes

**Method 1: Version Comparison**
```python
def detect_artifact_changes(app, artifact_type):
    current_export = export_artifacts(app, artifact_type)
    previous_export = load_previous_baseline(app, artifact_type)
    
    changes = compare_exports(current_export, previous_export)
    
    for change in changes:
        log_change({
            'artifact': change.name,
            'type': change.type,  # ADD/UPDATE/DELETE
            'old_hash': change.previous_hash,
            'new_hash': change.current_hash,
            'diff_summary': change.summary,
            'detected_at': datetime.now(),
            'sox_material': is_sox_material(change)
        })
```

**Method 2: Modified Date Tracking**
```python
def check_recent_modifications(app, artifact_type, since):
    artifacts = list_artifacts(app, artifact_type)
    
    recent_changes = [
        a for a in artifacts 
        if a.modified_date > since
    ]
    
    return extract_details(recent_changes)
```

**Method 3: EDM-Driven (Master Data)**
```python
def track_edm_driven_changes():
    # EDM is the source
    edm_requests = get_edm_requests(since=yesterday)
    
    for request in edm_requests:
        if request.status == 'APPROVED':
            # Track downstream deployments
            deployments = get_downstream_deployments(request.id)
            
            for dep in deployments:
                log_artifact_change({
                    'source': 'EDM',
                    'source_request': request.id,
                    'target_app': dep.application,
                    'deployment_id': dep.id,
                    'artifacts_affected': dep.changed_artifacts
                })
```

---

## Extraction Schedule by Artifact Type

### High Frequency (Daily/Per-Event)

| Artifact | Trigger | Why |
|----------|---------|-----|
| EDM Requests | On approval | Metadata changes flow downstream |
| Data Exchange Loads | After execution | Data integrity validation |
| Failed Deployments | Immediate alert | Fix before close |
| Policy Violations | Immediate alert | Governance issue |
| FCCS Period Status | During close | Close progression |

### Medium Frequency (Weekly)

| Artifact | Day | Why |
|----------|-----|-----|
| Consolidation Rules | Monday | Week-start baseline |
| Business Rules | Wednesday | Mid-week check |
| Forms | Friday | End-of-week summary |
| Security/Access | Sunday | Weekly review prep |
| Mapping Versions | Sunday | Documentation refresh |

### Low Frequency (Monthly/Quarterly)

| Artifact | Frequency | Why |
|----------|-----------|-----|
| Full Artifact Inventory | Monthly | Compliance snapshot |
| Complete Mapping Docs | Monthly | Up-to-date documentation |
| EDM Full Export | Monthly | Complete backup |
| Cross-Reference Check | Quarterly | Validate consistency |
| SOX Evidence Package | Quarterly | External audit support |

---

## Cross-Application Impact Analysis

**When EDM Changes:**
```
EDM Account Added
  ├─→ FCCS: Dimension import required
  ├─→ PBCS: Forms may need update
  ├─→ ARCS: Reconciliation profile may need update
  ├─→ Data Exchange: GL mapping check required
  └─→ PCM: Allocation rules impact?
```

**When Data Exchange Mapping Changes:**
```
Mapping Updated
  ├─→ Validate: Previous loads still reconciled?
  ├─→ Test: New mapping with sample data
  ├─→ Document: Update mapping documentation
  └─→ Notify: Downstream users of change
```

**When FCCS Rule Changes:**
```
Consolidation Rule Updated
  ├─→ Test: Run on test environment
  ├─→ Validate: Results match expected
  ├─→ Archive: Previous rule version
  ├─→ Document: Change justification
  └─→ Approve: Controller sign-off
```

---

## Next: Specific Extraction Scripts

Ready to build:
1. **FCCS Artifact Modification Export** (enhanced with full diffs)
2. **Data Exchange Mapping Audit** (with before/after validation)
3. **EDM Complete Change History** (with downstream impact)
4. **PBCS Forms Version Tracker** (layout comparisons)
5. **Cross-Application Consistency Checker** (EDM vs deployed metadata)

Which specific artifact type should I script first?
