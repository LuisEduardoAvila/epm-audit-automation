# EPM Application Artifact Audit Automation

*Automated extraction of artifact changes, mappings, and metadata modifications across Oracle EPM Cloud applications*

> **🔄 Migration in Progress**
> 
> **From:** Python scripts → **To:** ODI 12c → Oracle Autonomous DB → Retool
>
> - Baseline (Python): `v1.0-python-baseline` [GitHub Tag](https://github.com/LuisEduardoAvila/epm-audit-automation/releases/tag/v1.0-python-baseline)
> - Migration Plan: `openspec/changes/epm-odi-autonomous-retool/`
> - Status: Phase 1 (Foundation) - Database schema and ODI artifacts created
>
> **What's New:**
> - Oracle Autonomous Database schema with unified artifact storage
> - ODI 12c mapping and package templates in `odi-artifacts/`
> - Retool dashboard configuration in `retool/`
> - SOX-compliant audit trail via Oracle Data Safe


---

## Project Focus

**NOT:** User access, IAM, infrastructure  
**YES:** Application artifacts, business logic, mappings, forms that change

## What You're Already Doing Manually

| Manual Task | Automation Target | Apps |
|-------------|-------------------|------|
| Export Artifact Modification Report | Scheduled API extraction | All EPM |
| Track mapping changes | Data Exchange/ODI audit logs | Data Exchange |
| Document form modifications | Form version history export | PBCS, FCCS |
| Rule change tracking | Business rule versioning | FCCS, PBCS, PCM |
| Metadata/dimension changes | EDM request history + dimension audit | EDM, all apps |

---

## Scope by Application

### FCCS (Financial Consolidation and Close)

**Track These Artifacts:**

| Artifact Type | API Endpoint | What Changes | Audit Relevance |
|--------------|--------------|--------------|-----------------|
| **Consolidation Rules** | `/calculations` | Calculation logic, member formulas | How numbers are calculated |
| **Journals** | `/journals` | Journal templates, posting rules | Manual entries, adjustments |
| **Data Forms** | `/dataforms` | Form layout, access, validation rules | Data entry controls |
| **Dimensions** | `/dimensions/{dim}/members` | Account changes, entity additions | Chart of accounts |
| **Rulesets** | `/rulesets` | Rule execution order | Processing sequence |
| **Attribute Definitions** | `/attributes` | Custom attributes on members | Classification changes |
| **Exchange Rates** | `/rates` | Rate tables, historical rates | Translation accuracy |
| **Smart Lists** | `/smartlists` | Drop-down values | User input options |

**Specific Reports to Automate:**
- Artifact Modification Report (daily)
- Dimension Audit Report (whenever dimension deployed)
- Business Rule Execution Log (per calculation cycle)
- Journal Entry Detail (reversing, adjustments)

---

### PBCS (Planning and Budgeting)

**Track These Artifacts:**

| Artifact Type | API Endpoint | What Changes | Audit Relevance |
|--------------|--------------|--------------|-----------------|
| **Data Forms (Grids)** | `/applications/{app}/forms` | Layout, formulas, access | Planning input controls |
| **Business Rules** | `/businessrules` | Calc scripts, member formulas | Calculated values |
| **Planning Unit Hierarchy** | `/approvals/dimensions` | Approval workflows | Who approves what |
| **Task Lists** | `/tasklists` | Close tasks, dependencies | Process steps |
| **User Variables** | `/uservariables` | User context settings | Access scope |
| **Smart Lists** | `/smartlists` | Drop-down values | Input options |
| **Substitution Variables** | `/substitutionvariables` | Global variables | Cross-form logic |
| **Currency Tables** | `/currencies` | Exchange rates | Currency conversion |

**Specific Reports:**
- Forms Modification History (tracks layout changes)
- Approval Unit Audit (who changed approval paths)
- Business Rule Audit (scripts executed)

---

### EDM (Enterprise Data Management)

**Primary Source for ALL Metadata Changes**

| Change Type | API/Export | What It Captures | Audit Value |
|-------------|-----------|------------------|-------------|
| **Request History** | `/requests` | Who submitted/approved what change | Full workflow |
| **Hierarchy Versions** | `/views/{view}/versions` | Point-in-time snapshots | Rollback capability |
| **Node Property Changes** | `/nodes/{node}/properties` | Attribute modifications | Data quality |
| **Orphaned Nodes** | `/views/{view}/orphans` | Unmapped members | Data integrity |
| **Policy Violations** | `/policies/violations` | Governance rule breaks | Compliance issues |
| **Import/Export Jobs** | `/jobs` | Bulk loads, data feeds | Data lineage |

**Key Extraction:**
```
EDM Request = Complete audit trail of metadata changes
├── Submitter: who requested
├── Approver: who approved  
├── Timestamp: when
├── Change type: Add/Update/Delete
├── Properties: what changed
├── Before/After: values
├── Status: Approved/Rejected/Pending
└── Comments: why
```

**This feeds ALL other apps** - if an Account or Entity changes, it originates here.

---

### Data Exchange (Integration)

**Mapping Audit - Critical for Data Integrity**

| Component | What to Extract | Audit Purpose |
|-----------|----------------|---------------|
| **Data Load Rules** | Source-to-target mappings | How data transforms |
| **Execution Logs** | Success/failure per run | Data load evidence |
| **Error Records** | Failed records, rejections | Data quality issues |
| **Mapping Documentation** | Source column → Target member | Transformation logic |
| **Import Formats** | File layouts, delimiters | Format specifications |
| **Validation Rules** | Data quality checks | Integrity controls |

**Specific Artifacts:**
```
Data Exchange Mapping = Source to Target Transformation
├── Source System: GL, HR, Subledger
├── Source Table/File: AP_INVOICES, JE_LINES
├── Target Application: FCCS, PBCS, etc.
├── Mapping Logic: ACCOUNT = CASE WHEN...END
├── Transformation: Currency conversion, sign flipping
├── Validation RULES: Required fields, data types
├── Execution Schedule: Daily, monthly
└── Last Run Status: Success/Warning/Failed
```

**Critical for SOX:**
- Prove data loaded from source = data received in EPM
- Track every transformation applied
- Document rejected records and why
- Show who scheduled/executed loads

---

### ARCS (Account Reconciliation)

**Track These Artifacts:**

| Artifact Type | API/Export | What Changes | Audit Relevance |
|--------------|-----------|--------------|-----------------|
| **Reconciliation Formats** | `/reconciliations/formats` | Format templates | Visual presentation |
| **Transaction Rules** | `/reconciliations/rules` | Auto-matching logic | Automation accuracy |
| **Profiles** | `/reconciliations/profiles` | Profile assignments | Who reconciles what |
| **Compliance Rules** | `/reconciliations/compliance` | Auto-certification rules | Control automation |
| **Currency Pairs** | `/currencypairs` | Rate configurations | FX accuracy |

---

### PCM (Profitability Management)

**Track These Artifacts:**

| Artifact Type | API/Export | What Changes | Audit Relevance |
|--------------|-----------|--------------|-----------------|
| **Allocation Rules** | `/allocations` | Cost allocation logic | Cost distribution |
| **Stages** | `/stages` | Flow definitions | Processing order |
| **Drivers** | `/drivers` | Allocation basis | Cost drivers |
| **Traceability** | `/trace` | Audit trails | Source to result |

---

## Artifact Modification Report Structure

### What Oracle Provides (Manual Export)

**Artifact Modification Report columns:**
```csv
Artifact_Name, Artifact_Type, Modified_By, Modified_Date, 
Old_Value, New_Value, Comments
```

### What We Automate

**Enhanced Artifact Audit:**
```json
{
  "artifact_id": "Consol_Rule_01",
  "artifact_name": "Eliminate_Intercompany",
  "artifact_type": "Consolidation_Rule",
  "application": "FCCS_Production",
  "modified_by": "john.smith@company.com",
  "modified_date": "2026-02-25T14:32:00Z",
  "change_type": "UPDATE",
  "old_value_hash": "a3f5...",
  "new_value_hash": "b8d2...",
  "diff_summary": "Added entity filter [100, 200]",
  "comments": "Q1 restructure - exclude new entities",
  "approver": "jane.doe@company.com",
  "approval_date": "2026-02-25T16:00:00Z",
  "related_changes": ["EDM_Request_12345"],
  "sox_critical": true
}
```

---

## Data Exchange Mapping Audit

### Mapping Change Tracking

**Before/After Comparison**

```yaml
Mapping: GL_Account_to_FCCS_Account
Version: 2.1 (Changed 2026-02-25)
Changed_By: data.admin@company.com
Approved_By: finance.controller@company.com

Before (v2.0):
  Source: GL.ACCOUNT
  Transformation: 
    CASE 
      WHEN GL.ACCOUNT LIKE '1%' THEN '1000'
      WHEN GL.ACCOUNT LIKE '2%' THEN '2000'
    END

After (v2.1):
  Source: GL.ACCOUNT  
  Transformation:
    CASE
      WHEN GL.ACCOUNT LIKE '1%' THEN '1000'
      WHEN GL.ACCOUNT LIKE '2%' THEN '2000'
      WHEN GL.ACCOUNT LIKE '3%' THEN '3000'  -- NEW: Added for Q1
    END

Impact:
  Records_Affected: 15,230 new mappings
  Periods_Impacted: 2026-01 onwards
  Validation: Pass (98.5% match to source)
```

### Critical Checks

**Data Exchange Validation:**
- Source record count = Target record count
- Hash totals match (sum of amounts)
- Rejected records analyzed
- Transformation errors logged
- Execution duration trending

---

## Forms Modification Audit

### PBCS/FCCS Forms

**What Changes:**
```yaml
Form: DataEntry_WorkingBudget
Modified: 2026-02-20
By: budget.admin@company.com

Changes:
  Layout:
    - Added: Version member (Working/Submitted)
    - Removed: OldScenario column
  Rows:
    - Reordered: Account hierarchy
    - Added: NewCostCenter group
  Validations:
    - New: Max check on line items
    - Changed: Budget cap validation
  Security:
    - Updated: Read access to Regional_Managers group
    - Removed: Finance_Operations group
  Formulas:
    - Updated: Total formula to include new rows
```

---

## Automation Schedule

### Daily (During Month-End)

**All Extractions:**
- Artifact Modification Report (full export)
- Data Exchange execution logs (success/failure)
- EDM request status (approved/rejected/pending)
- Failed data loads (immediate alert)

### Weekly

- Forms modification summary
- Business rule execution performance
- Mapping version changes
- Reconciliation format updates

### Per-Event (Triggered by Change)

- Dimension deployment → Full dimension audit
- Application update → Full artifact baseline
- Data Exchange rule change → Mapping diff report
- EDM request approved → Downstream impact analysis

### Monthly/Quarterly

- Complete artifact inventory
- All mapping documentation refresh
- Cross-reference EDM→FCCS→PBCS changes
- SOX evidence package generation

---

## Integration Points

**EDM is the Source of Truth:**
```
EDM Request Approved
    ↓
Triggers: FCCS Dimension Import
    ↓
Updates: Chart of Accounts
    ↓
Requires: Data Exchange mapping update
    ↓
Impacts: FCCS Forms, PBCS Forms, ARCS Profiles
```

**Automated Dependency Tracking:**
- When EDM Account changes, flag FCCS rules using that account
- When Data Exchange mapping changes, validate downstream loads
- When Form changes, notify users of that form
- When Rule changes, document calculation impact

---

## Output Examples

### 1. Artifact Change Summary (Daily Email)

```
EPM Artifact Changes - 2026-02-26
====================================

FCCS Production:
  Consolidation Rules Changed: 2
    - Eliminate_IC (Modified by: j.smith)
    - Currency_Translation (No material change)
  
  Data Forms Modified: 1
    - JournalEntry_Form (Added validation rule)

PBCS Planning:  
  Business Rules Updated: 3
    - Calc_Headcount (Formula updated)
    - Rollup_Salary (No logic change)
    - Allocation_Overhead (NEW - requires approval)

EDM:
  Requests Approved: 5
    - Cost Center restructure (Impacts: FCCS, PBCS)
    - Account additions Q1 (Impacts: FCCS only)
  
  Pending Approval: 2
    - Entity hierarchy (Waiting: controller approval)

Data Exchange:
  Mapping Changes: 1
    - GL_to_FCCS_AP (Added account range 3000-3999)
    - Load Success Rate: 99.2% (5 failures analyzed)

ACTION REQUIRED:
- Review PBCS rule "Allocation_Overhead" before next cycle
- Validate Data Exchange mapping for Q1 accounts
```

### 2. Detailed Artifact Diff Report

```
ARTIFACT: FCCS_Consolidation_Rule
NAME: Eliminate_Intercompany
CHANGED: 2026-02-25 14:32:00
BY: john.smith@company.com

CHANGES DETECTED:
-----------------
Line 45: Added condition
  [IF]: @ISMBR("Entity":["100","200"])
  [THEN]: SKIP
  [REASON]: Exclude newly acquired entities from elimination

APPROVAL:
Approver: jane.doe@company.com
Date: 2026-02-25 16:00:00
Comments: "Approved per Q1 integration plan"

IMPACT ANALYSIS:
- Entities Affected: 100 (NewCo), 200 (SubCo)
- Intercompany Accounts: 1210, 2110
- Periods: 2026-01 onwards
- Test Case: PASS (elimination balances with manual calc)

SOX CLASSIFICATION: Material Change
```

---

## Configuration Requirements

### What We Need From You

**Per Application:**
- EPM REST API endpoint URLs
- Service account credentials (with appropriate artifact read permissions)
- Data Exchange environment details (if separate from FCCS)
- EDM application ID
- Artifact types you care most about (prioritize if too many)

**Mapping Documentation:**
- Current manual export schedule (so we match it)
- Distribution list for change alerts
- Materiality thresholds (what changes need manager approval)
- Related system dependencies (EDM→FCCS→etc.)

---

## Next Steps

1. **Identify your current manual exports** (which reports you run weekly/monthly)
2. **List your critical artifacts** (which apps/types matter most for audit)
3. **Set up service accounts** with artifact read permissions
4. **Test extraction** for top 3-5 artifacts
5. **Automate alerts** when artifacts change

Want me to create the specific extraction scripts for:
- **FCCS Artifact Modification Report** (full endpoint mapping)
- **Data Exchange mapping audit** (with before/after diff)
- **EDM request automation** (complete metadata change history)
- **PBCS Forms tracking** (version comparison)

Which app/type should we start with?
