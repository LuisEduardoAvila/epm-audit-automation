# Artifact Materiality Filter

*Pre-populated controls for SOX-compliant artifact change classification*

## Overview

The `materiality_filter.py` module provides pre-configured classification rules to distinguish **operational noise** (period opens, consolidation runs) from **material configuration changes** (rule edits, form modifications) that require audit attention.

## Quick Start

```python
from scripts.materiality_filter import ArtifactMaterialityFilter, ChangeClassifier

# Initialize filter
filter = ArtifactMaterialityFilter()

# Classify a single change
change = {
    'application': 'FCCS',
    'artifact_name': 'Eliminate_IC_Rule',
    'artifact_type': 'consolidation_rule',
    'modified_by': 'john.smith@company.com',
    'operation': 'UPDATE',
    'change_type': 'FORMULA_EDIT',
    'changed_fields': ['formula', 'member_scope', 'last_updated']
}

result = filter.classify_change(change)

# Check materiality
if result['material']:
    print(f"🔴 MATERIAL CHANGE: {result['alert_severity']}")
    print(f"Reasoning: {result['reasoning']}")
else:
    print("ℹ️  Operational noise - no action needed")
```

## Classification Results

```
{
    'category': 'sox_critical',           # operational_state | configuration_change | sox_critical | unknown
    'material': True,                      # True = requires audit attention
    'sox_relevant': True,                  # True = SOX compliance impact
    'requires_approval': True,             # True = needs documented approval
    'alert_severity': 'high',              # info | low | medium | high | critical
    'confidence': 0.95,                    # Classification confidence 0.0-1.0
    'reasoning': ['Configuration fields modified',
                  "Artifact type 'consolidation_rule' is SOX-critical"],
    'recommendations': ['Requires immediate controller review and approval documentation'],
    'event': {...}                         # Original event data
}
```

## Pre-Populated Rules

### Change Categories

| Category | Material | SOX Relevant | Example |
|----------|----------|--------------|---------|
| **OPERATIONAL_STATE** | ❌ No | ❌ No | Period opened, consolidation run, journal posted |
| **CONFIGURATION_CHANGE** | ✅ Yes | ✅ Yes | Form layout edited, mapping rule changed |
| **SOX_CRITICAL** | ✅ Yes | ✅ Yes | Consolidation rule formula edited, hierarchy modified |
| **UNKNOWN** | ⚠️ Review needed | ⚠️ Review needed | Unable to classify automatically |

### Operational Fields (Noise)

Changes to these fields are **NOT material**:

```python
OPERATIONAL_FIELDS = {
    'status', 'last_run_time', 'last_run_by', 'execution_status',
    'period_status', 'close_status', 'certification_status',
    'request_status', 'deployment_status', 'run_count',
    'last_updated', 'modified_timestamp', 'version_timestamp',
    'last_accessed', 'access_count', 'execution_count',
    'workflow_status', 'approval_status', 'submission_status'
}
```

### Configuration Fields (Material)

Changes to these fields **ARE material**:

```python
CONFIGURATION_FIELDS = {
    'formula', 'script', 'calculation_logic', 'definition',
    'layout', 'structure', 'configuration', 'settings',
    'member_scope', 'hierarchy', 'validation_rules',
    'source_mapping', 'target_mapping', 'transformation_logic',
    'properties', 'attributes', 'parent_id', 'relationships',
    'calculation_order', 'condition', 'aggregation_rule'
}
```

### SOX-Critical Artifact Types

These artifact types **always** trigger SOX-critical classification:

- `consolidation_rule`
- `business_rule`
- `calculation_rule`
- `journal_template`
- `approval_unit`
- `hierarchy`
- `validation_rule`
- `matching_rule`
- `mapping_rule`
- `security_filter`

## Application-Specific Patterns

### FCCS

**Operational (Noise):**
- Period opened/closed/locked
- Consolidation run completed
- Journal posted
- Translation executed
- Form accessed

**Material (Audit):**
- Consolidation rule formula edited
- Member moved in hierarchy
- Form layout changed
- Journal template structure modified
- Exchange rate table updated

```python
# Example: FCCS Period Open (NOISE)
{
    'application': 'FCCS',
    'artifact_name': 'Period_Feb_2026',
    'artifact_type': 'PERIOD',
    'operation': 'OPEN',
    'changed_fields': ['status', 'last_updated']
}
# Result: operational_state, material=False

# Example: FCCS Rule Edit (SOX CRITICAL)
{
    'application': 'FCCS',
    'artifact_name': 'Eliminate_IC_Rule',
    'artifact_type': 'consolidation_rule',
    'operation': 'UPDATE',
    'changed_fields': ['formula', 'member_scope', 'last_updated']
}
# Result: sox_critical, material=True, severity=high
```

### PBCS

**Operational (Noise):**
- Form data saved
- Planning unit promoted
- Calculation ran
- Task checked off
- Approval submitted

**Material (Audit):**
- Business rule script edited
- Form definition changed
- Approval hierarchy modified
- Substitution variable changed
- Security filter edited

### EDM

**Operational (Noise):**
- Request submitted/approved/completed
- Deployment successful
- View cache refreshed
- Import job ran

**Material (Audit):**
- Node moved in hierarchy
- Node properties changed
- Governance policy modified
- Mapping rule edited
- Hierarchy structure changed

### Data Exchange

**Operational (Noise):**
- Load executed
- Export ran
- Scheduled job completed
- Error reprocessing

**Material (Audit):**
- Load rule mapping edited
- Import format changed
- Validation rule modified
- Period/category mapping changed
- Transformation logic updated

## Batch Processing

```python
from scripts.materiality_filter import ArtifactMaterialityFilter

filter = ArtifactMaterialityFilter()

# Process multiple changes
changes = [
    {...},  # Period open
    {...},  # Rule edit
    {...},  # Form layout change
    {...},  # Deployment complete
]

results = filter.filter_changes(changes, include_noise=False)

# Results structure:
{
    'material': [...],           # Configuration changes
    'sox_critical': [...],       # SOX-critical changes
    'unknown': [...],            # Need manual review
    'summary': {
        'total': 4,
        'material': 2,
        'sox_critical': 1,
        'noise': 1
    }
}

# Extract only SOX-critical for immediate attention
sox_critical = results['sox_critical']
for change in sox_critical:
    alert_controller(change)
```

## Integration with Extraction Scripts

### Example: FCCS Artifact Extractor

```python
from scripts.materiality_filter import ArtifactMaterialityFilter
from scripts.credential_manager import CredentialManager

class FCCSArtifactExtractor:
    def __init__(self):
        self.materiality_filter = ArtifactMaterialityFilter()
    
    def extract_and_classify(self, since_date):
        # Extract all changes
        all_changes = self._extract_fccs_changes(since_date)
        
        # Classify
        classified = self.materiality_filter.filter_changes(
            all_changes,
            include_noise=False  # Skip operational
        )
        
        # Generate report
        report = {
            'extraction_date': datetime.now().isoformat(),
            'total_changes': classified['summary']['total'],
            'material_changes': classified['summary']['material'],
            'sox_critical': classified['summary']['sox_critical'],
            'changes': classified['sox_critical'] + classified['material']
        }
        
        # Alert on SOX-critical
        if classified['summary']['sox_critical'] > 0:
            self._alert_sox_critical(classified['sox_critical'])
        
        return report
```

## SOX Materiality Rules Summary

### Always Material

These changes **always** require audit documentation:

| Change Type | Requires Approval | Evidence Required |
|-------------|-------------------|-------------------|
| Consolidation rule formula change | ✅ Yes | Before/after formula, approver sign-off |
| Business rule script change | ✅ Yes | Script diff, testing evidence |
| Approval hierarchy modification | ✅ Yes | New hierarchy, approval chain |
| Access control change | ✅ Yes | Security review, business justification |
| Validation rule modification | ✅ Yes | Rule change, test results |
| Chart of accounts structure change | ✅ Yes | New structure, migration plan |
| Journal template structure change | ✅ Yes | Template diff, approval |

### Conditionally Material

These **may** be material depending on context:

| Change Type | Material If... |
|-------------|----------------|
| Member attribute change | Affects consolidation, intercompany, or data storage |
| Form layout change | Removes validation, affects calculation order |
| Mapping rule change | Source system change, affects financial statements |

### Never Material

These changes are **cosmetic only**:

- Label/form text changes
- Translation updates
- Sort order adjustments
- Display preferences
- Color/formatting changes

## Alert Thresholds

| Severity | Trigger | Action |
|----------|---------|--------|
| **CRITICAL** | SOX-critical change unapproved | Immediate email to controller |
| **HIGH** | SOX-critical change detected | Daily digest with details |
| **MEDIUM** | Material change detected | Daily digest |
| **LOW** | Unknown classification | Weekly summary, manual review |
| **INFO** | Operational noise | Log only, no alert |

## Testing the Filter

```bash
# Run built-in test
cd /path/to/epm-audit-automation
python scripts/materiality_filter.py

# Expected output:
# Period_Feb_2026 → operational_state (NOISE)
# Eliminate_IC_Rule → sox_critical (MATERIAL)
# Annual_Budget_Form → configuration_change (MATERIAL)
# Add_Entity_100 → operational_state (NOISE)
```

## Extending the Rules

Add custom classification rules:

```python
from scripts.materiality_filter import ChangeClassifier

classifier = ChangeClassifier()

# Add custom operational field
classifier.OPERATIONAL_FIELDS.add('custom_status_field')

# Add custom configuration field
classifier.CONFIGURATION_FIELDS.add('custom_logic_field')

# Add custom SOX-critical artifact
classifier.SOX_CRITICAL_ARTIFACTS.add('custom_critical_type')

# Re-classify with new rules
result = classifier.classify_change(event)
```

## Integration with Alerting

```python
# Email notification for SOX-critical changes
if result['alert_severity'] == 'critical':
    send_email(
        to='controller@company.com',
        subject=f"🔴 SOX-Critical Change: {artifact_name}",
        body=format_alert(result)
    )

# Slack notification for material changes
if result['material']:
    post_slack(
        channel='#epm-audit-alerts',
        message=format_slack_alert(result)
    )

# Create Jira ticket for tracking
if result['requires_approval']:
    create_jira_ticket(
        project='SOX',
        summary=f"EPM Change: {artifact_name}",
        description=format_jira_description(result)
    )
```

## File Reference

| File | Purpose |
|------|---------|
| `scripts/materiality_filter.py` | Classification engine and rules |
| `docs/change-classification.md` | Detailed change classification documentation |
| `docs/artifact-extraction-matrix.md` | API endpoints and extraction patterns |

## Next Steps

1. **Integrate into extraction scripts:**
   ```python
   from materiality_filter import ArtifactMaterialityFilter
   filter = ArtifactMaterialityFilter()
   ```

2. **Configure alert destinations:**
   - Email: controller, audit team
   - Slack: #epm-audit-alerts
   - Jira: SOX project

3. **Test with real data:**
   - Run against test environment first
   - Validate classification accuracy
   - Tune rules if needed

4. **Document exceptions:**
   - Create override rules if needed
   - Document business justification

---

*Pre-loaded with 50+ classification rules across 6 EPM applications*
