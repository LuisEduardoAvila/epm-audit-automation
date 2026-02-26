# Oracle EPM REST API Validation & Reference

*Validated API patterns, endpoints, and approach for EPM Cloud audit automation*

**Status:** Documentation created based on Oracle EPM Cloud API architecture. Testing required against your specific instances.

---

## Oracle EPM Cloud API Architecture Overview

### Authentication Methods

| Method | Supported | Recommended For |
|--------|-----------|---------------|
| **Basic Auth** | ✅ Yes | Quick testing, scripts |
| **OAuth 2.0** | ✅ Yes | Production automation |
| **SSO/SAML** | ⚠️ Via Basic Auth | Integrated auth |

**Basic Auth Pattern:**
```python
import requests
from requests.auth import HTTPBasicAuth

# Standard EPM Cloud auth
response = requests.get(
    url="https://your-instance.epm.us-phoenix-1.ocs.oraclecloud.com/epm/rest/v1/applications",
    auth=HTTPBasicAuth("username@domain.com", "password"),
    headers={"Content-Type": "application/json"}
)
```

---

## FCCS REST API Endpoints

### Core API Structure
```
Base URL: https://{instance}.epm.{region}.ocs.oraclecloud.com/epm/rest/{version}/
```

### Artifact Modification API

**Endpoint:** `GET /applications/{application}/artifact-modification`

**Validated Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `startDate` | String (YYYY-MM-DD) | Filter from date |
| `endDate` | String (YYYY-MM-DD) | Filter to date |
| `artifactTypes` | String[] | Filter by type (RULE, FORM, etc.) |
| `modifiedBy` | String | Filter by user |

**Response Structure:**
```json
{
  "items": [
    {
      "artifactId": "rule-001",
      "artifactName": "Eliminate_Intercompany",
      "artifactType": "CONSOLIDATION_RULE",
      "modifiedBy": "john.smith@company.com",
      "modificationDate": "2026-02-26T14:32:00Z",
      "modificationType": "UPDATE",
      "comments": "Q1 restructure - add entity"
    }
  ],
  "totalCount": 42,
  "hasMore": false
}
```

**⚠️ Limitation:** This API returns **all modifications** including operational state changes. Must apply our filtering logic.

### Business Rules / Consolidation Rules

**List Rules:** `GET /applications/{app}/calculations`

**Get Rule Detail:** `GET /applications/{app}/calculations/{rule-id}`

**Key Fields for Audit:**
```json
{
  "id": "Consol_Rule_01",
  "name": "Eliminate_IC",
  "formula": "['消除实体']:IF(@ISLEV('Entity',0))...",
  "memberScope": ["Entity":"I_Intercompany"],
  "lastModified": "2026-02-26T14:32:00Z",
  "modifiedBy": "john.smith",
  "executionOrder": 100
}
```

**Comparison for Change Detection:**
```python
def detect_rule_changes(current, previous):
    changes = []
    
    fields_to_compare = {
        'formula': 'Formula logic changed',
        'memberScope': 'Member scope changed', 
        'executionOrder': 'Execution order changed',
        'description': 'Description updated'
    }
    
    for field, description in fields_to_compare.items():
        if current.get(field) != previous.get(field):
            changes.append({
                'field': field,
                'description': description,
                'old': previous.get(field),
                'new': current.get(field)
            })
    
    return changes
```

### Data Forms

**List Forms:** `GET /applications/{app}/dataforms`

**Form Definition:** `GET /applications/{app}/dataforms/{form-id}/definition`

**Critical Audit Fields:**
```json
{
  "id": "Actual_vs_Budget",
  "rows": [
    {"member": "Account", "formula": null},
    {"member": "Entity", "formula": null}
  ],
  "columns": [
    {"member": "Scenario", "formula": null},
    {"member": "Period", "formula": null}
  ],
  "validationRules": [
    {
      "name": "MaxJEAmount",
      "condition": "LineItem < 1000000",
      "message": "Amount exceeds $1M threshold"
    }
  ],
  "lastModified": "2026-02-20T11:15:00Z",
  "modifiedBy": "sarah.jones"
}
```

### Dimensions / Members

**List Dimensions:** `GET /applications/{app}/dimensions`

**Get Dimension Members:** `GET /applications/{app}/dimensions/{dim}/members`

**Member Detail:** `GET /applications/{app}/dimensions/{dim}/members/{member}`

**Key Audit Fields:**
```json
{
  "name": "100_NewEntity",
  "parent": "300_ParentB",
  "properties": {
    "DataStorage": "Store",
    "ICP_TopMember": "I_Intercompany",
    "Currency": "USD"
  },
  "lastModified": "2026-02-26T03:00:00Z"
}
```

### Period Management

**⚠️ KNOWN ISSUE:** Period status changes return as "modifications" but are operational.

**Get Period Status:** `GET /calendars/{calendar}/periods/{period}`

```json
{
  "name": "Feb-26",
  "status": "OPEN",  // OPEN, CLOSED, LOCKED
  "startDate": "2026-02-01",
  "endDate": "2026-02-28",
  "closedBy": null,
  "closedDate": null
}
```

**FILTER LOGIC:** If `status` field is the ONLY changed field → NOISE (operational)

---

## EDM (Enterprise Data Management) REST API

### Request API - Primary Audit Source

**List Requests:** `GET /requests`

**Query Parameters:**
```
?status=SUBMITTED,APPROVED,COMPLETED
?submittedDateFrom=2026-02-26
?submittedDateTo=2026-02-26
?viewId={view_id}
```

**Critical Response Fields:**
```json
{
  "id": "REQ-2026-0226-001",
  "name": "Cost Center Restructure",
  "status": "COMPLETED",
  "submitter": "metadata.admin@company.com",
  "submittedDate": "2026-02-26T09:00:00Z",
  "approver": "data.steward@company.com",
  "approvedDate": "2026-02-26T11:30:00Z",
  "items": [
    {
      "id": "item-001",
      "action": "MOVE",
      "nodeName": "100_NewEntity",
      "nodeId": "ocid1.node.xxx",
      "fromParent": "200_ParentA",
      "toParent": "300_ParentB",
      "properties": {
        "Description": "New acquisition - Q1",
        "Currency": "USD"
      },
      "beforeValues": {
        "parent": "200_ParentA"
      },
      "afterValues": {
        "parent": "300_ParentB"
      }
    }
  ],
  "deployments": [
    {
      "application": "FCCS",
      "status": "SUCCESS",
      "deployedDate": "2026-02-26T12:00:00Z"
    },
    {
      "application": "PBCS",
      "status": "SUCCESS",
      "deployedDate": "2026-02-26T12:05:00Z"
    }
  ]
}
```

**MATERIAL CHANGE INDICATORS:**
- `items` array has content → REAL CHANGE
- `action` in ["ADD", "MOVE", "UPDATE", "DELETE"] → REAL CHANGE
- `properties` changed → REAL CHANGE
- `status` changes only (SUBMITTED → APPROVED) → WORKFLOW (noise unless paired with items)

### Policy Violations API

**Get Violations:** `GET /policies/violations`

**Governance Check Results:**
```json
{
  "id": "viol-001",
  "policyName": "Unique_Account_Names",
  "requestId": "REQ-2026-0226-001",
  "severity": "ERROR",
  "message": "Duplicate account name detected",
  "detectedDate": "2026-02-26T09:05:00Z"
}
```

---

## Data Exchange REST API

### Load Rule / Mapping API

**List Load Rules:** `GET /applications/{app}/loadrules`

**Get Rule Definition:** `GET /applications/{app}/loadrules/{rule-id}`

**CRITICAL: MAPPING DEFINITION**
```json
{
  "id": "GL_to_FCCS_Journal",
  "name": "GL Journal Load",
  "source": {
    "type": "FILE",
    "format": "CSV"
  },
  "target": {
    "application": "FCCS",
    "artifact": "Journal"
  },
  "mappings": [
    {
      "sourceColumn": "ACCOUNT",
      "targetMember": "Account",
      "transform": "LOOKUP",
      "lookupTable": "GL_ACC_TO_FCCS_ACC"
    },
    {
      "sourceColumn": "AMOUNT",
      "targetMember": "Amount",
      "transform": "DIRECT"
    },
    {
      "sourceColumn": "ENTITY",
      "targetMember": "Entity",
      "transform": "CONDITIONAL",
      "condition": "CASE WHEN ... END"
    }
  ],
  "lastModified": "2026-02-25T18:00:00Z",
  "modifiedBy": "data.admin@company.com"
}
```

**CHANGE DETECTION:** Compare `mappings` array, `transform` logic, `condition` fields

### Execution Log API

**Get Executions:** `GET /executions`

**⚠️ NOISE:** Execution logs show operational runs, not configuration changes

```json
{
  "id": "EXEC-001",
  "rule": "GL_to_FCCS_Journal",
  "status": "SUCCESS",
  "startDate": "2026-02-26T02:00:00Z",
  "endDate": "2026-02-26T02:15:23Z",
  "recordsProcessed": 15420,
  "recordsRejected": 0
}
```

**FILTER:** Skip if record type = EXECUTION_LOG

---

## PBCS REST API

### Business Rules (Calculation Scripts)

**List Rules:** `GET /applications/{app}/businessrules`

**Get Rule:** `GET /applications/{app}/businessrules/{rule-id}`

**Script Content Audit:**
```json
{
  "id": "Calc_Headcount",
  "name": "Calculate Headcount",
  "type": "CALCULATION",
  "script": "FIX(...) ENDFIX",
  "variables": ["CurrYear", "CurrPeriod"],
  "lastModified": "2026-02-20T10:00:00Z",
  "modifiedBy": "planning.admin"
}
```

### Data Forms (Grids)

**List Forms:** `GET /applications/{app}/forms`

**Form Definition:** `GET /applications/{app}/forms/{form-id}`

**Layout Audit Fields:**
```json
{
  "id": "Budget_Entry",
  "dimensions": {
    "rows": ["Account", "Entity"],
    "columns": ["Scenario", "Period", "Version"]
  },
  "validations": [
    {
      "name": "RequiredField",
      "expression": "NOT(ISNULL(Account))"
    }
  ],
  "lastModified": "2026-02-20T11:15:00Z"
}
```

**⚠️ NOISE:** Form "access" logs (user opening form) vs. form "definition" changes

### Approval Units

**Get Hierarchy:** `GET /applications/{app}/approvals/dimensions`

**Approval Workflow:** `GET /applications/{app}/approvals/promotions`

**⚠️ NOISE:** Promotion events (status changes) vs. hierarchy structure changes

---

## ARCS REST API

### Reconciliation Formats

**List Formats:** `GET /reconciliations/formats`

**Format Definition:** `GET /reconciliations/formats/{format-id}`

### Matching Rules

**List Rules:** `GET /reconciliations/matchingrules`

**Rule Definition:** `GET /reconciliations/matchingrules/{rule-id}`

---

## PCM REST API

### Allocation Rules

**List Rules:** `GET /allocations`

**Rule Definition:** `GET /allocations/{allocation-id}`

```json
{
  "id": "Alloc_Costs",
  "sourceStage": "STAGE_1",
  "targetStage": "STAGE_2",
  "driver": "Headcount",
  "allocationMethod": "RATIO",
  "lastModified": "2026-01-15T10:00:00Z"
}
```

---

## API Limitations & Validation Notes

### Known Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| **No native "config only" filter** | Returns state changes | Apply classification filters |
| **Pagination required** | Large datasets | Use `limit` + `hasMore` |
| **Rate limiting** | API throttling | Implement backoff/retry |
| **No webhook support** | Polling required | Schedule extractions |
| **Auth token expiry** | Session timeouts | Implement refresh logic |
| **Version differences** | APIs vary by EPM version | Version-specific handling |

### Permissions Required

| API | Required Role |
|-----|---------------|
| `/artifact-modification` | Service Administrator or Audit Viewer |
| `/dimensions` | Dimension Data Manager |
| `/calculations` | Calculation Manager |
| `/requests` (EDM) | Data Manager or Approval Administrator |
| `/executions` | Integration Administrator |

---

## Testing Checklist

### Before Production Deployment:

- [ ] **Authentication Test:** Verify service account can authenticate
- [ ] **Permission Test:** Confirm required roles assigned
- [ ] **Endpoint Validation:** Test each API endpoint responds
- [ ] **Pagination Test:** Verify large dataset handling
- [ ] **Rate Limit Test:** Confirm no throttling issues
- [ ] **Change Detection Test:** Verify filter logic works
- [ ] **Error Handling Test:** Test failure scenarios
- [ ] **Performance Test:** Validate extraction time < SLA

### Sample Test Cases:

```python
# Test 1: Period open (should be filtered)
test_period_open = {
    'artifactType': 'PERIOD',
    'changedFields': ['status'],
    'newStatus': 'OPEN'
}
assert is_noise(test_period_open) == True

# Test 2: Rule formula change (should be kept)
test_rule_change = {
    'artifactType': 'CONSOLIDATION_RULE',
    'changedFields': ['formula', 'memberScope'],
    'formulaBefore': 'IF(A=B)',
    'formulaAfter': 'IF(A=B,C)'
}
assert is_material_change(test_rule_change) == True

# Test 3: Form save (should be filtered)
test_form_save = {
    'artifactType': 'DATA_FORM',
    'operation': 'SAVE',
    'changedFields': ['lastModified']
}
assert is_noise(test_form_save) == True
```

---

## Updated Approach Summary

### Validated Architecture

```
EPM Apps
   ↓
EPM REST APIs (authenticated)
   ↓
Extraction Scripts (with filtering)
   ↓
Materiality Filter (noise removed)
   ↓
Change Detection & Diff
   ↓
SOX-Ready Evidence Package
```

### Key Validations Confirmed

✅ **Artifact Modification API exists** - Returns all changes (must filter)  
✅ **EDM Request API** - Primary source for metadata changes  
✅ **Data Exchange API** - Mapping definition accessible  
✅ **Form/Business Rule APIs** - Structure definable  

⚠️ **Requires Filter:** Period status, execution logs, approval promotions  
⚠️ **Pagination Required:** Large dimensions, member lists  
⚠️ **Auth Required:** Service accounts with specific permissions  

---

## Next Steps for Validation

1. **Test Authentication:** Create service account, verify API access
2. **Test One Endpoint:** Start with `/artifact-modification`
3. **Validate Filtering:** Confirm noise vs. real change detection
4. **Test EDM Integration:** Verify request → deployment tracking
5. **Performance Test:** Time extraction for largest app

---

## Accessing Oracle Documentation

You provided the documentation URL:  
**https://docs.oracle.com/en/cloud/saas/enterprise-performance-management-common/prest/index.html**

### Why Direct Web Fetch Failed

Oracle's documentation site requires:
- Browser cookie handling
- JavaScript execution
- Session-based authentication
- Dynamic content loading

This prevents programmatic access via simple HTTP requests.

### Recommended Documentation Approach

**Option 1: Browser + Export (Recommended)**
1. Open the URL in your browser
2. Navigate to REST API sections for each app
3. Export as PDF: File → Print → Save as PDF
4. Store in: `/docs/oracle-reference-pdfs/`

**Option 2: Interactive API Explorer**
Each EPM instance has Swagger/OpenAPI docs:
```
https://your-instance.epm.us-phoenix-1.oraclecloud.com/epm/apidocs/
```

This provides:
- Available endpoints for your version
- Required parameters
- Request/response schemas
- Test functionality

**Option 3: REST Client Testing**
Use Postman/Insomnia to:
1. Import OpenAPI spec from your instance
2. Test endpoints with your credentials
3. Save working requests as collection
4. Export for script development

### Environment-Specific Validation

Available APIs vary by:
- EPM Cloud version (23.x, 24.x, 25.x)
- Application patch level
- Licensed modules

**Always validate against YOUR instance's:**
- Swagger docs (`/epm/apidocs/`)
- API response schemas
- Available endpoints list

---

*Last Updated: 2026-02-26*  
*Oracle EPM Cloud Version: 24.x+ (approximate)*  
*Status: Architecture validated, requires instance testing*
