# EPM Artifact Change Classification

*Distinguishing configuration changes from operational state changes*

## The Problem

**What Manual Exports Capture:**
```
"Journal Period Feb-26 modified by user SYSTEM"
→ Actually means: Period was OPENED for data entry
→ NOT: Journal configuration changed

"Consolidation Rule Balance_Flow run completed"
→ Actually means: Rule was EXECUTED
→ NOT: Rule formula was modified

"Data Form Actual_Vs_Budget updated"
→ Actually means: Form was ACCESSED/SAVED
→ NOT: Form layout/calculations changed
```

**Result:** Audit reports full of noise, real changes buried.

---

## Change Classification System

### Level 1: Operational State Changes (NOT Audit-Relevant)

| App | Activity | What It Looks Like | Actual Meaning |
|-----|----------|-------------------|----------------|
| **FCCS** | Period state changed | Period "modified" | User opened/locked period |
| **FCCS** | Consolidation run | Rule "executed" | Standard calc cycle |
| **FCCS** | Journal posted | Journal template "touched" | Transaction processed |
| **PBCS** | Form saved | Form "updated" | Data entry completed |
| **PBCS** | Approval promoted | Planning unit "changed" | Workflow advanced |
| **PBCS** | Calculation ran | Business rule "triggered" | Standard calc |
| **EDM** | Request status | Request "modified" | Submitted → Approved |
| **EDM** | Deployment | View "updated" | Metadata pushed to app |
| **Data Exchange** | Load executed | Load rule "run" | Scheduled data import |
| **ARCS** | Rec certified | Reconciliation "updated" | Status = Certified |

**These are Operational Activities:**
- Expected daily/monthly activities
- Part of normal close/planning cycle
- **NOT audit exceptions** (unless unusual timing/pattern)

### Level 2: Configuration Changes (Audit-Relevant)

| App | Artifact | What Changed | Why It Matters |
|-----|----------|--------------|----------------|
| **FCCS** | Consolidation Rule | Formula logic, member scope | How numbers calculate |
| **FCCS** | Data Form | Layout, columns, formulas, validation | How data is entered/viewed |
| **FCCS** | Dimension | Member adds, moves, attribute changes | Chart of accounts |
| **FCCS** | Journal Template | Structure, validation rules | Journal entry controls |
| **FCCS** | Attribute | Custom attributes on members | Classification logic |
| **FCCS** | Smart List | Values available to users | Input options |
| **PBCS** | Business Rule | Calculation script, loops | How values compute |
| **PBCS** | Form Definition | Grid layout, POV, formulas | Planning input controls |
| **PBCS** | Approval Unit | Who approves what hierarchy | Delegation of authority |
| **PBCS** | Substitution Variable | Global variable values | Cross-form logic |
| **EDM** | Hierarchy/Request | Node moves, property changes | Master data structure |
| **EDM** | Policy | Governance rules, validations | Data quality controls |
| **EDM** | Mapping | Cross-system mappings | Data integration logic |
| **Data Exchange** | Load Rule | Source-to-target mapping logic | Data transformation |
<br>
| **Data Exchange** | Import Format | File layout, delimiters | How data is read |
| **Data Exchange** | Validation Rule | Required fields, ranges | Data integrity checks |
| **ARCS** | Format | Reconciliation layout | Presentation rules |
| **ARCS** | Matching Rule | Auto-match criteria | Automation logic |
| **PCM** | Allocation Rule | Source→Target assignment | Cost distribution |

**These ARE Configuration Changes:**
- Change *how* the system works
- Impact financial calculations or data integrity
- Require approval and documentation
- **Audit exceptions** if unapproved

---

## Filtering Logic

### How to Detect Real vs. Noise

#### Method 1: Modified Fields Analysis

```python
def classify_change(artifact_change):
    """
    Analyze what fields changed to determine materiality
    """
    
    change = artifact_change
    
    # Check modified fields
    modified_fields = change.get('modified_fields', [])
    
    # NOISE: Only state/execution fields changed
    operational_fields = {
        'status', 'last_run_time', 'last_run_by', 'execution_status',
        'period_status', 'close_status', 'certification_status',
        'request_status', 'deployment_status', 'run_count',
        'last_updated'  # metadata timestamp update only
    }
    
    # MATERIAL: Configuration fields changed
    config_fields = {
        'formula', 'script', 'definition', 'layout', 'mapping',
        'member_scopes', 'validation_rules', 'properties',
        'hierarchy', 'parent_id', 'attribute_values',
        'source_mapping', 'transformation_logic', 'condition',
        'calculation_order', 'dependencies'
    }
    
    # Determine classification
    has_operational = any(f in operational_fields for f in modified_fields)
    has_config = any(f in config_fields for f in modified_fields)
    
    if has_config:
        return {
            'category': 'CONFIGURATION_CHANGE',
            'material': True,
            'requires_approval': True,
            'sox_relevant': True,
            'alert_severity': 'HIGH'
        }
    elif has_operational:
        return {
            'category': 'OPERATIONAL_STATE',
            'material': False,
            'requires_approval': False,
            'sox_relevant': False,
            'alert_severity': 'INFO'
        }
    else:
        return {
            'category': 'UNKNOWN',
            'material': False,
            'requires_review': True
        }
```

#### Method 2: API Endpoint Patterns

```python
def classify_by_endpoint(api_call):
    """
    Determine if API call is configuration or operational
    """
    
    endpoint = api_call.get('endpoint', '')
    http_method = api_call.get('method', 'GET')
    
    # Operational endpoints (noise)
    operational_patterns = [
        '/periods/.*?(open|close|lock)',
        '/consolidations/run',
        '/journals/.*?/post',
        '/approvals/.*?/promote',
        '/requests/.*?/(submit|approve|reject)',
        '/executions/run',
        '/forms/.*?/(save|submit)',
        '/loads/.*?/(execute|run)',
        '/reconciliations/.*?/certify'
    ]
    
    # Configuration endpoints (material)
    config_patterns = [
        '/calculations/.*?/(update|delete|create)',
        '/forms/.*?/(update|delete|create)',
        '/businessrules/.*?(update|delete|create)',
        '/dimensions/.*?/members/(add|remove|update)',
        '/mappings/.*?/(update|delete|create)',
        '/loadrules/.*?/(update|delete|create)',
        '/policies/.*?/(update|delete|create)',
        '/attributes/.*?/(update|delete|create)'
    ]
    
    # Check patterns
    import re
    
    for pattern in operational_patterns:
        if re.search(pattern, endpoint):
            return 'OPERATIONAL'
    
    for pattern in config_patterns:
        if re.search(pattern, endpoint):
            return 'CONFIGURATION'
    
    # HTTP method hints
    if http_method in ['POST', 'PUT', 'DELETE']:
        # Could be either - check body
        return 'REQUIRES_ANALYSIS'
    
    return 'UNKNOWN'
```

#### Method 3: Content Hash Comparison

```python
def detect_real_change(artifact, previous_export):
    """
    Compare artifact content to detect actual changes
    """
    
    current_content = artifact.get('definition')
    previous_content = previous_export.get('definition')
    
    # Calculate content hashes
    import hashlib
    
    current_hash = hashlib.sha256(
        json.dumps(current_content, sort_keys=True).encode()
    ).hexdigest()
    
    previous_hash = hashlib.sha256(
        json.dumps(previous_content, sort_keys=True).encode()
    ).hexdigest()
    
    if current_hash == previous_hash:
        # Only metadata changed (timestamp, etc)
        return {
            'real_change': False,
            'reason': 'METADATA_ONLY',
            'fields_changed': ['last_modified', 'modified_by']
        }
    else:
        # Real content changed
        diff = calculate_diff(previous_content, current_content)
        return {
            'real_change': True,
            'reason': 'CONTENT_CHANGED',
            'diff': diff,
            'changed_sections': identify_changed_sections(diff)
        }
```

---

## Specific Filters by Application

### FCCS Noise vs. Real Changes

| Activity | Detection Pattern | Classification |
|----------|-------------------|----------------|
| Period opened | Period status → OPEN | **NOISE** (Operational) |
| Period closed | Period status → CLOSED | **NOISE** (Operational) |
| Consolidation run | Job log shows EXECUTE | **NOISE** (Operational) |
| Rule formula edited | Rule body changed | **REAL** (Config) |
| Member moved | Parent changed | **REAL** (Config) |
| View saved | Form accessed | **NOISE** (Operational) |
| Form layout edited | Grid definition changed | **REAL** (Config) |
| Journal posted | Status POSTED | **NOISE** (Operational) |
| Journal template changed | Template structure modified | **REAL** (Config) |
| Translation run | Job log: TRANSLATE | **NOISE** (Operational) |
| Rate table updated | Rate values changed | **REAL** (Config) |

**FCCS Filter Query:**
```python
def fccs_filter(change):
    # Skip period state changes
    if change.get('object_type') == 'PERIOD' and \
       'status' in change.get('changed_fields', []):
        return False  # NOISE
    
    # Skip job executions
    if change.get('object_type') == 'CONSOLIDATION_JOB':
        return False  # NOISE
    
    # Skip journal postings
    if change.get('object_type') == 'JOURNAL' and \
       change.get('change_type') == 'STATUS_CHANGE':
        return False  # NOISE
    
    # Keep actual configuration changes
    return True
```

---

### PBCS Noise vs. Real Changes

| Activity | Detection Pattern | Classification |
|----------|-------------------|----------------|
| Form data saved | User submitted data | **NOISE** (Operational) |
| Form layout changed | Row/column/formula modified | **REAL** (Config) |
| Calculation ran | Script executed | **NOISE** (Operational) |
| Calculation script edited | Rule formula changed | **REAL** (Config) |
| Planning unit promoted | Approval status advanced | **NOISE** (Operational) |
| Approval hierarchy changed | Approval unit structure | **REAL** (Config) |
| Task checked off | Task list updated | **NOISE** (Operational) |
| Task list structure modified | Tasks/steps changed | **REAL** (Config) |
| Variable value set | Substitution var changed | **REAL** (Config) |
| Data pushed to cube | Integration run | **NOISE** (Operational) |

**PBCS Filter Query:**
```python
def pbcs_filter(change):
    # Skip form saves (data entry)
    if change.get('object_type') == 'DATA_FORM' and \
       change.get('operation') == 'SAVE':
        return False  # NOISE - data entry
    
    # Keep form definition changes
    if change.get('object_type') == 'DATA_FORM' and \
       'definition' in change.get('changed_fields', []):
        return True  # REAL - form structure
    
    # Skip execution logs
    if change.get('operation') == 'EXECUTE':
        return False  # NOISE - calc run
    
    # Keep rule changes
    if change.get('object_type') == 'BUSINESS_RULE' and \
       change.get('operation') == 'UPDATE':
        return True  # REAL - rule edited
    
    # Skip promotion/approval workflow
    if change.get('operation') == 'PROMOTE':
        return False  # NOISE - approval flow
    
    return True
```

---

### EDM Noise vs. Real Changes

| Activity | Detection Pattern | Classification |
|----------|-------------------|----------------|
| Request submitted | Status → IN_PROGRESS | **NOISE** (Operational) |
| Request approved | Status → APPROVED | **NOISE** (Operational) |
| Request deployed | Status → COMPLETED | **NOISE** (Operational) |
| Node moved | Node.parent changed | **REAL** (Config) |
| Property updated | Node.property changed | **REAL** (Config) |
| View refreshed | Cache rebuilt | **NOISE** (Operational) |
| Policy validated | Violation check | **NOISE** (Operational) |
| Policy rule modified | Policy definition changed | **REAL** (Config) |
| Import job run | Batch load executed | **NOISE** (Operational) |
| Mapping rule edited | Mapping logic changed | **REAL** (Config) |

**EDM Filter Query:**
```python
def edm_filter(request_or_change):
    # Status changes are operational
    if len(request_or_change.get('items', [])) == 0:
        # No actual content changes, just status
        return False  # NOISE
    
    # Check if any nodes/properties actually changed
    has_content_change = False
    for item in request_or_change.get('items', []):
        if item.get('action') in ['ADD', 'MOVE', 'UPDATE', 'DELETE']:
            if item.get('node_id') or item.get('property_changes'):
                has_content_change = True
                break
    
    if not has_content_change:
        return False  # NOISE - pure workflow
    
    return True  # REAL - metadata changed
```

---

### Data Exchange Noise vs. Real Changes

| Activity | Detection Pattern | Classification |
|----------|-------------------|----------------|
| Load executed | Execution log only | **NOISE** (Operational) |
| Load failed | Error status | **NOISE** (Operational) |
| Mapping edited | Transformation logic changed | **REAL** (Config) |
| Import format modified | File layout changed | **REAL** (Config) |
| Period map updated | Date→Period mapping | **REAL** (Config) |
| Validation rule added/removed | Data quality rule | **REAL** (Config) |
| Category mapping | Scenario mapping | **REAL** (Config) |
| Scheduled run | Recurrence execution | **NOISE** (Operational) |

**Data Exchange Filter Query:**
```python
def dataexchange_filter(change):
    # Skip execution logs
    if change.get('record_type') == 'EXECUTION_LOG':
        return False  # NOISE
    
    # Keep mapping changes
    if change.get('record_type') in ['LOAD_RULE', 'MAPPING']:
        return True  # REAL
    
    # Keep format changes
    if change.get('record_type') in ['IMPORT_FORMAT', 'VALIDATION_RULE']:
        return True  # REAL
    
    # Skip scheduled runs
    if change.get('trigger_type') == 'SCHEDULED':
        return False  # NOISE
    
    return True
```

---

## Output: Clean Audit Trail

### Before Filtering (Noisy)
```
ALERT: 47 changes detected in FCCS Production (2026-02-26)

1. Period Feb-26 OPENED by SYSTEM (14:32)
2. Consolidation run completed for Feb-26 (02:15)
3. Journal JRNL_00124 POSTED by j.smith (09:45)
4. Form Actual_Vs_Budget SAVED by j.doe (11:20)
5. Period Jan-26 LOCKED by controller (10:00)
...
```

### After Filtering (Clean)
```
ALERT: 3 MATERIAL CHANGES detected in FCCS Production (2026-02-26)

═══════════════════════════════════════════════════════
🔴 CONFIGURATION CHANGE 1
Artifact: Consolidation Rule "Eliminate_IC"
Changed By: john.smith@company.com
Time: 2026-02-26 14:32:00Z
Action: FORMULA_EDITED

CHANGED_FIELDS: ['formula_logic', 'member_scope']
BEFORE: Entities: [100, 200, 300]
AFTER: Entities: [100, 200, 300, 400]  # 400 added
APPROVER: jane.doe@company.com
COMMENTS: "Q1 integration - add NewCo entity"

SOX IMPACT: Material - affects consolidation
STATUS: Approved, Documented

═══════════════════════════════════════════════════════
🔴 CONFIGURATION CHANGE 2
Artifact: Data Form "Journal_Entry"
Changed By: sarah.jones@company.com
Time: 2026-02-26 11:15:00Z
Action: LAYOUT_MODIFIED

CHANGED_FIELDS: ['validation_rule']
ADDED: Max check on line items ($1M threshold)
APPROVER: mike.brown@company.com
COMMENTS: "Strengthen JE controls per audit finding"

SOX IMPACT: Medium - validation enhancement
STATUS: Approved

═══════════════════════════════════════════════════════
🟡 CONFIGURATION CHANGE 3
Artifact: Dimension "Account"
Changed By: SYSTEM (EDM deploy)
Time: 2026-02-26 03:00:00Z
Action: MEMBER_ADDED

ADDED: Account "3999_Temp_Reclass"
EDM_REQUEST: REQ-2026-0226-001
APPROVER: data.guardian@company.com

SOX IMPACT: Low - new account creation
STATUS: Approved, Deployed
═══════════════════════════════════════════════════════
```

---

## Implementation: Filters in Extraction Scripts

### Universal Filter Function

```python
class ArtifactMaterialityFilter:
    """
    Filters operational noise from configuration changes
    """
    
    # Operational signatures by app
    NOISE_PATTERNS = {
        'FCCS': {
            'status_changes': ['OPEN', 'CLOSED', 'LOCKED', 'UNLOCKED'],
            'operations': ['RUN', 'EXECUTE', 'POST', 'CERTIFY'],
            'object_types': ['PERIOD', 'CONSOLIDATION_JOB', 'JOURNAL']
        },
        'PBCS': {
            'operations': ['SAVE', 'SUBMIT', 'PROMOTE', 'EXECUTE'],
            'object_types': ['DATA_ENTRY', 'PLANNING_UNIT_PROMOTION']
        },
        'EDM': {
            'status_only': True,  # If only status field changed
            'workflow_stages': ['SUBMITTED', 'APPROVED', 'REJECTED', 'COMPLETED']
        },
        'DATA_EXCHANGE': {
            'execution_only': True,
            'executed_by': ['SYSTEM', 'SCHEDULER']
        }
    }
    
    def is_material_change(self, change_event):
        """
        Determine if change is material (config) vs noise (operational)
        """
        app = change_event.get('application')
        
        # Check if real content changed
        content_fields = self._get_content_fields(change_event)
        metadata_only = self._is_metadata_only(change_event)
        
        if metadata_only:
            return False  # Noise
        
        if not content_fields:
            return False  # No actual changes
        
        # Check app-specific patterns
        if self._is_operational_signature(app, change_event):
            return False  # Noise
        
        return True  # Material change
    
    def _get_content_fields(self, event):
        """Extract fields that changed actual content"""
        changed = event.get('changed_fields', [])
        
        # Content fields vary by artifact type
        content_field_patterns = {
            'RULE': ['formula', 'script', 'calculation_logic'],
            'FORM': ['layout', 'definition', 'rows', 'columns'],
            'MAPPING': ['source', 'target', 'transformation'],
            'DIMENSION': ['members', 'hierarchy', 'properties'],
            'TEMPLATE': ['structure', 'fields', 'validations']
        }
        
        # Find matching pattern
        for artifact_type, fields in content_field_patterns.items():
            if event.get('artifact_type') == artifact_type:
                return [f for f in changed if any(p in f for p in fields)]
        
        return changed  # Default: all fields
    
    def _is_metadata_only(self, event):
        """Check if only timestamps/metadata changed"""
        metadata_fields = {'last_modified', 'modified_by', 'last_run', 
                          'version_timestamp', 'run_count'}
        
        changed = set(event.get('changed_fields', []))
        
        return changed.issubset(metadata_fields)
    
    def _is_operational_signature(self, app, event):
        """Check against app-specific operational patterns"""
        patterns = self.NOISE_PATTERNS.get(app, {})
        
        # Check operations
        if event.get('operation') in patterns.get('operations', []):
            return True
        
        # Check status changes
        if event.get('change_type') == 'STATUS_CHANGE':
            if event.get('new_status') in patterns.get('status_changes', []):
                return True
        
        # Check object types
        if event.get('object_type') in patterns.get('object_types', []):
            return True
        
        # Check workflow-only changes
        if patterns.get('status_only'):
            if self._is_status_only_change(event):
                return True
        
        return False
    
    def _is_status_only_change(self, event):
        """Check if only workflow status changed"""
        changed = set(event.get('changed_fields', []))
        return changed == {'status'}
```

---

## Usage in Extraction

```python
# During extraction
filter = ArtifactMaterialityFilter()

all_changes = extract_fccs_artifacts(since=yesterday)

# Filter to material changes only
material_changes = [
    c for c in all_changes 
    if filter.is_material_change(c)
]

# Create alert
if material_changes:
    send_alert({
        'severity': 'HIGH' if any(is_sox_critical(c) for c in material_changes) else 'MEDIUM',
        'count': len(material_changes),
        'changes': material_changes,
        'filtered_out': len(all_changes) - len(material_changes)
    })

# Daily summary
daily_report = {
    'total_events': len(all_changes),
    'operational_noise': len(all_changes) - len(material_changes),
    'material_changes': len(material_changes),
    'sox_critical': sum(1 for c in material_changes if is_sox_critical(c)),
    'requires_approval': sum(1 for c in material_changes if not c.get('approved'))
}
```

---

## Summary

| Classification | What It Means | Action |
|----------------|---------------|--------|
| **NOISE** | Operational activity (period open, calc run, approval) | Log only, no alert unless anomaly |
| **MATERIAL** | Configuration changed (rules, forms, mappings) | Alert, require approval, document |
| **SOX_CRITICAL** | Material + affects financials/controls | Immediate alert, escalation, evidence |

**Result:** Clean audit trail with **only changes that matter**.

---

*Last Updated: 2026-02-26*
*Purpose: Eliminate noise from EPM artifact audit reports*
