#!/usr/bin/env python3
"""
EPM Artifact Materiality Filter

Pre-populated controls for classifying artifact changes.
Distinguishes operational noise from configuration changes requiring audit attention.

Usage:
    from materiality_filter import ArtifactMaterialityFilter, ChangeClassifier
    
    filter = ArtifactMaterialityFilter()
    classification = filter.classify_change(change_event)
    
    if classification['material']:
        alert_audit_team(change_event, classification)
"""

import re
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from datetime import datetime


class ChangeCategory(Enum):
    """Classification categories for changes"""
    OPERATIONAL_STATE = "operational_state"
    CONFIGURATION_CHANGE = "configuration_change"
    SOX_CRITICAL = "sox_critical"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ChangeEvent:
    """Represents an artifact change event"""
    application: str
    artifact_name: str
    artifact_type: str
    modified_by: str
    modified_date: datetime
    operation: str
    change_type: str
    changed_fields: List[str] = field(default_factory=list)
    old_values: Dict = field(default_factory=dict)
    new_values: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'application': self.application,
            'artifact_name': self.artifact_name,
            'artifact_type': self.artifact_type,
            'modified_by': self.modified_by,
            'modified_date': self.modified_date.isoformat(),
            'operation': self.operation,
            'change_type': self.change_type,
            'changed_fields': self.changed_fields,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'metadata': self.metadata
        }


@dataclass
class ClassificationResult:
    """Result of change classification"""
    category: ChangeCategory
    material: bool
    sox_relevant: bool
    requires_approval: bool
    alert_severity: AlertSeverity
    confidence: float
    reasoning: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class ChangeClassifier:
    """
    Pre-populated classification rules for EPM artifact changes.
    
    Based on SOX compliance requirements and audit best practices.
    """
    
    # === OPERATIONAL FIELDS (Noise) ===
    # Changes to these fields are typically operational, not configuration
    OPERATIONAL_FIELDS: Set[str] = {
        'status', 'last_run_time', 'last_run_by', 'execution_status',
        'period_status', 'close_status', 'certification_status',
        'request_status', 'deployment_status', 'run_count',
        'last_updated', 'modified_timestamp', 'version_timestamp',
        'last_accessed', 'access_count', 'execution_count',
        'workflow_status', 'approval_status', 'submission_status',
        'post_status', 'certify_status', 'lock_status'
    }
    
    # === CONFIGURATION FIELDS (Material) ===
    # Changes to these fields indicate configuration changes
    CONFIGURATION_FIELDS: Set[str] = {
        'formula', 'script', 'calculation_logic', 'definition',
        'layout', 'structure', 'configuration', 'settings',
        'member_scope', 'member_selection', 'hierarchy',
        'validation_rules', 'validation_logic', 'constraints',
        'source_mapping', 'target_mapping', 'transformation_logic',
        'properties', 'attributes', 'metadata_values',
        'parent_id', 'child_ids', 'relationships',
        'calculation_order', 'execution_sequence', 'dependencies',
        'condition', 'criteria', 'filter_logic',
        'aggregation_rule', 'consolidation_logic'
    }
    
    # === SOX CRITICAL ARTIFACT TYPES ===
    # Changes to these always require audit attention
    SOX_CRITICAL_ARTIFACTS: Set[str] = {
        'consolidation_rule', 'business_rule', 'calculation_rule',
        'journal_template', 'approval_unit', 'hierarchy',
        'validation_rule', 'matching_rule', 'mapping_rule',
        'security_filter', 'access_rule'
    }
    
    # === APP-SPECIFIC NOISE PATTERNS ===
    NOISE_PATTERNS: Dict[str, Dict[str, Any]] = {
        'FCCS': {
            'status_changes': ['OPEN', 'CLOSED', 'LOCKED', 'UNLOCKED', 'FROZEN'],
            'operations': ['RUN', 'EXECUTE', 'POST', 'CERTIFY', 'CONSOLIDATE'],
            'object_types': ['PERIOD', 'CONSOLIDATION_JOB', 'JOURNAL', 'TRANSLATION_JOB'],
            'noise_indicators': [
                r'Period.*?(opened|closed|locked)',
                r'Consolidation.*?(completed|run)',
                r'Journal.*?(posted|submitted)',
                r'Translation.*?(completed|run)'
            ]
        },
        'PBCS': {
            'status_changes': ['SUBMITTED', 'APPROVED', 'REJECTED', 'PROMOTED'],
            'operations': ['SAVE', 'SUBMIT', 'PROMOTE', 'EXECUTE', 'CALCULATE'],
            'object_types': ['DATA_ENTRY', 'PLANNING_UNIT_PROMOTION', 'FORM_SUBMISSION'],
            'noise_indicators': [
                r'Form.*?(saved|submitted)',
                r'Planning unit.*?(promoted|approved)',
                r'Calculation.*?(completed|run)',
                r'Task.*?(completed|checked)'
            ]
        },
        'EDM': {
            'status_changes': ['SUBMITTED', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'COMPLETED'],
            'operations': ['SUBMIT', 'APPROVE', 'REJECT', 'DEPLOY'],
            'object_types': ['REQUEST', 'DEPLOYMENT', 'IMPORT_JOB'],
            'noise_indicators': [
                r'Request.*?(submitted|approved|completed)',
                r'Deployment.*?(successful|completed)',
                r'Import.*?(completed|run)'
            ]
        },
        'DATA_EXCHANGE': {
            'status_changes': ['RUNNING', 'COMPLETED', 'FAILED', 'WARNING'],
            'operations': ['EXECUTE', 'RUN', 'LOAD'],
            'object_types': ['EXECUTION_LOG', 'LOAD_RUN', 'SCHEDULED_JOB'],
            'noise_indicators': [
                r'Load.*?(completed|executed)',
                r'Export.*?(completed|run)',
                r'Execution.*?(successful|failed)'
            ]
        },
        'ARCS': {
            'status_changes': ['PREPARED', 'CERTIFIED', 'UNCERTIFIED', 'REOPENED'],
            'operations': ['CERTIFY', 'UNCERTIFY', 'PREPARE'],
            'object_types': ['RECONCILIATION', 'TRANSACTION_MATCH'],
            'noise_indicators': [
                r'Reconciliation.*?(certified|prepared)',
                r'Match.*?(run|completed)'
            ]
        },
        'PCM': {
            'status_changes': ['RUNNING', 'COMPLETED', 'FAILED'],
            'operations': ['ALLOCATE', 'RUN', 'CALCULATE'],
            'object_types': ['ALLOCATION_RUN', 'STAGE_CALCULATION'],
            'noise_indicators': [
                r'Allocation.*?(completed|run)',
                r'Stage.*?(calculated|processed)'
            ]
        }
    }
    
    # === SOX CRITICAL CHANGE PATTERNS ===
    SOX_CRITICAL_PATTERNS: List[str] = [
        r'(?i)(consolidation|calculation|allocation).{0,20}(rule|logic|formula)',
        r'(?i)(approval|hierarchy).{0,20}(unit|workflow)',
        r'(?i)(validation|matching).{0,20}(rule|logic)',
        r'(?i)access.{0,20}(control|rule|filter)',
        r'(?i)(journal|form).{0,20}(template|structure)',
        r'(?i)(mapping|transformation).{0,20}(rule|logic)'
    ]
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for performance"""
        self._sox_patterns = [re.compile(p) for p in self.SOX_CRITICAL_PATTERNS]
        
        self._noise_patterns = {}
        for app, config in self.NOISE_PATTERNS.items():
            self._noise_patterns[app] = [re.compile(p) for p in config.get('noise_indicators', [])]
    
    def classify_change(self, event: ChangeEvent) -> ClassificationResult:
        """
        Classify a change event based on pre-populated rules.
        
        Returns ClassificationResult with materiality assessment.
        """
        reasoning = []
        recommendations = []
        
        # Step 1: Check if purely operational
        if self._is_operational_change(event):
            reasoning.append("Change is purely operational (state/execution related)")
            return ClassificationResult(
                category=ChangeCategory.OPERATIONAL_STATE,
                material=False,
                sox_relevant=False,
                requires_approval=False,
                alert_severity=AlertSeverity.INFO,
                confidence=0.95,
                reasoning=reasoning,
                recommendations=recommendations
            )
        
        # Step 2: Check field-level materiality
        field_analysis = self._analyze_changed_fields(event)
        
        # Step 3: Check artifact type
        artifact_sox_critical = self._is_sox_critical_artifact(event)
        
        # Step 4: Determine category and severity
        if field_analysis['has_configuration_changes'] or artifact_sox_critical:
            category = ChangeCategory.SOX_CRITICAL if artifact_sox_critical else ChangeCategory.CONFIGURATION_CHANGE
            material = True
            requires_approval = True
            
            if artifact_sox_critical:
                alert_severity = AlertSeverity.HIGH
                reasoning.append(f"Artifact type '{event.artifact_type}' is SOX-critical")
                recommendations.append("Requires immediate controller review and approval documentation")
            else:
                alert_severity = AlertSeverity.MEDIUM
                reasoning.append("Configuration fields modified")
            
            sox_relevant = True
            
        elif field_analysis['has_operational_changes']:
            category = ChangeCategory.OPERATIONAL_STATE
            material = False
            sox_relevant = False
            requires_approval = False
            alert_severity = AlertSeverity.INFO
            reasoning.append("Only operational fields modified")
            
        else:
            category = ChangeCategory.UNKNOWN
            material = False
            sox_relevant = False
            requires_approval = False
            alert_severity = AlertSeverity.LOW
            reasoning.append("Unable to determine change materiality - manual review recommended")
            recommendations.append("Review change manually to determine audit relevance")
        
        # Add field analysis to reasoning
        if field_analysis.get('config_fields'):
            reasoning.append(f"Configuration fields: {', '.join(field_analysis['config_fields'])}")
        if field_analysis.get('operational_fields'):
            reasoning.append(f"Operational fields: {', '.join(field_analysis['operational_fields'])}")
        
        return ClassificationResult(
            category=category,
            material=material,
            sox_relevant=sox_relevant,
            requires_approval=requires_approval,
            alert_severity=alert_severity,
            confidence=field_analysis.get('confidence', 0.8),
            reasoning=reasoning,
            recommendations=recommendations
        )
    
    def _is_operational_change(self, event: ChangeEvent) -> bool:
        """Check if change is purely operational based on app-specific patterns"""
        app = event.application.upper()
        
        if app not in self.NOISE_PATTERNS:
            return False
        
        patterns = self._noise_patterns.get(app, [])
        
        # Check change description/summary
        change_text = f"{event.artifact_name} {event.operation} {event.change_type}"
        
        for pattern in patterns:
            if pattern.search(change_text):
                return True
        
        # Check status-only changes
        if self._is_status_only_change(event, app):
            return True
        
        return False
    
    def _is_status_only_change(self, event: ChangeEvent, app: str) -> bool:
        """Check if only status field changed"""
        changed = set(event.changed_fields)
        
        # If only status changed
        if changed == {'status'} or changed == {'status', 'last_updated'}:
            new_status = event.new_values.get('status', '').upper()
            app_config = self.NOISE_PATTERNS.get(app, {})
            
            if new_status in app_config.get('status_changes', []):
                return True
        
        return False
    
    def _analyze_changed_fields(self, event: ChangeEvent) -> Dict:
        """Analyze which fields changed and their materiality"""
        changed = set(event.changed_fields)
        
        config_fields = changed & self.CONFIGURATION_FIELDS
        operational_fields = changed & self.OPERATIONAL_FIELDS
        unknown_fields = changed - config_fields - operational_fields
        
        has_config = len(config_fields) > 0
        has_operational = len(operational_fields) > 0
        
        # Confidence calculation
        if has_config and not has_operational:
            confidence = 0.95
        elif has_config and has_operational:
            confidence = 0.85
        elif has_operational and not has_config:
            confidence = 0.90
        else:
            confidence = 0.50  # Unknown fields
        
        return {
            'has_configuration_changes': has_config,
            'has_operational_changes': has_operational and not has_config,
            'config_fields': list(config_fields),
            'operational_fields': list(operational_fields),
            'unknown_fields': list(unknown_fields),
            'confidence': confidence
        }
    
    def _is_sox_critical_artifact(self, event: ChangeEvent) -> bool:
        """Check if artifact type is SOX-critical"""
        artifact_type = event.artifact_type.lower().replace(' ', '_')
        
        if artifact_type in self.SOX_CRITICAL_ARTIFACTS:
            return True
        
        # Check name patterns
        for pattern in self._sox_patterns:
            if pattern.search(event.artifact_name):
                return True
        
        return False


class ArtifactMaterialityFilter:
    """
    High-level filter for batch processing artifact changes.
    
    Usage:
        filter = ArtifactMaterialityFilter()
        results = filter.filter_changes(change_events)
    """
    
    def __init__(self):
        self.classifier = ChangeClassifier()
    
    def classify_change(self, change_event: Dict) -> Dict:
        """
        Classify a single change event (dict format).
        
        Args:
            change_event: Dictionary with change data
            
        Returns:
            Classification result with materiality flag
        """
        event = self._dict_to_event(change_event)
        result = self.classifier.classify_change(event)
        
        return {
            'category': result.category.value,
            'material': result.material,
            'sox_relevant': result.sox_relevant,
            'requires_approval': result.requires_approval,
            'alert_severity': result.alert_severity.value,
            'confidence': result.confidence,
            'reasoning': result.reasoning,
            'recommendations': result.recommendations,
            'event': event.to_dict()
        }
    
    def filter_changes(self, change_events: List[Dict], 
                       include_noise: bool = False) -> Dict:
        """
        Filter a list of changes, separating material from noise.
        
        Args:
            change_events: List of change event dictionaries
            include_noise: If True, include operational changes in output
            
        Returns:
            Dictionary with 'material' and optionally 'noise' lists
        """
        results = {
            'material': [],
            'sox_critical': [],
            'noise': [],
            'unknown': [],
            'summary': {
                'total': len(change_events),
                'material': 0,
                'sox_critical': 0,
                'noise': 0,
                'unknown': 0
            }
        }
        
        for change in change_events:
            classification = self.classify_change(change)
            
            category = classification['category']
            
            if category == 'sox_critical':
                results['sox_critical'].append(classification)
                results['summary']['sox_critical'] += 1
            elif category == 'configuration_change':
                results['material'].append(classification)
                results['summary']['material'] += 1
            elif category == 'operational_state':
                if include_noise:
                    results['noise'].append(classification)
                results['summary']['noise'] += 1
            else:
                results['unknown'].append(classification)
                results['summary']['unknown'] += 1
        
        return results
    
    def _dict_to_event(self, data: Dict) -> ChangeEvent:
        """Convert dictionary to ChangeEvent"""
        modified_date = data.get('modified_date')
        if isinstance(modified_date, str):
            modified_date = datetime.fromisoformat(modified_date.replace('Z', '+00:00'))
        elif isinstance(modified_date, datetime):
            pass
        else:
            modified_date = datetime.now()
        
        return ChangeEvent(
            application=data.get('application', 'UNKNOWN'),
            artifact_name=data.get('artifact_name', 'Unknown'),
            artifact_type=data.get('artifact_type', 'Unknown'),
            modified_by=data.get('modified_by', 'System'),
            modified_date=modified_date,
            operation=data.get('operation', 'UPDATE'),
            change_type=data.get('change_type', 'UPDATE'),
            changed_fields=data.get('changed_fields', []),
            old_values=data.get('old_values', {}),
            new_values=data.get('new_values', {}),
            metadata=data.get('metadata', {})
        )


# === PRE-POPULATED CHANGE TYPE DEFINITIONS ===

# For use in classification rules and UI dropdowns
CHANGE_TYPE_DEFINITIONS = {
    'FCCS': {
        'operational': {
            'PERIOD_OPEN': 'Opened period for data entry',
            'PERIOD_CLOSE': 'Closed period',
            'PERIOD_LOCK': 'Locked period',
            'CONSOLIDATION_RUN': 'Executed consolidation',
            'TRANSLATION_RUN': 'Ran currency translation',
            'JOURNAL_POST': 'Posted journal entries',
            'FORM_ACCESS': 'Accessed data form'
        },
        'configuration': {
            'RULE_FORMULA_EDIT': 'Modified consolidation rule formula',
            'RULE_SCOPE_CHANGE': 'Changed rule member scope',
            'FORM_LAYOUT_EDIT': 'Modified form layout/structure',
            'MEMBER_MOVE': 'Moved dimension member',
            'MEMBER_ADD': 'Added new dimension member',
            'ATTRIBUTE_CHANGE': 'Modified member attributes',
            'TEMPLATE_EDIT': 'Changed journal template structure',
            'RATE_TABLE_UPDATE': 'Updated exchange rates',
            'SMART_LIST_EDIT': 'Modified smart list values'
        }
    },
    'PBCS': {
        'operational': {
            'FORM_SAVE': 'Saved form data',
            'DATA_SUBMIT': 'Submitted planning data',
            'UNIT_PROMOTE': 'Promoted planning unit',
            'CALCULATION_RUN': 'Executed business rule',
            'TASK_COMPLETE': 'Completed close task',
            'APPROVAL_SUBMIT': 'Submitted for approval'
        },
        'configuration': {
            'BUSINESS_RULE_EDIT': 'Modified calculation script',
            'FORM_DEFINITION_EDIT': 'Changed form definition',
            'APPROVAL_HIERARCHY_EDIT': 'Modified approval hierarchy',
            'SUBSTITUTION_VAR_CHANGE': 'Changed global variable',
            'SMART_LIST_EDIT': 'Modified smart list',
            'VALIDATION_RULE_EDIT': 'Changed validation logic',
            'SECURITY_FILTER_EDIT': 'Modified data access'
        }
    },
    'EDM': {
        'operational': {
            'REQUEST_SUBMIT': 'Submitted metadata request',
            'REQUEST_APPROVE': 'Approved metadata change',
            'REQUEST_DEPLOY': 'Deployed to applications',
            'REQUEST_REJECT': 'Rejected request',
            'VIEW_REFRESH': 'Refreshed view cache',
            'POLICY_CHECK': 'Ran policy validation'
        },
        'configuration': {
            'NODE_MOVE': 'Moved hierarchy node',
            'NODE_PROPERTY_CHANGE': 'Modified node properties',
            'NODE_ADD': 'Added new node',
            'NODE_REMOVE': 'Removed node',
            'POLICY_EDIT': 'Modified governance policy',
            'MAPPING_EDIT': 'Changed mapping rule',
            'HIERARCHY_CHANGE': 'Modified hierarchy structure',
            'RELATIONSHIP_EDIT': 'Changed node relationships'
        }
    },
    'DATA_EXCHANGE': {
        'operational': {
            'LOAD_EXECUTE': 'Executed data load',
            'EXPORT_RUN': 'Ran data export',
            'SCHEDULED_RUN': 'Automated execution',
            'ERROR_REPROCESS': 'Reprocessed failed records'
        },
        'configuration': {
            'MAPPING_EDIT': 'Modified load rule mapping',
            'IMPORT_FORMAT_EDIT': 'Changed file format',
            'VALIDATION_RULE_EDIT': 'Modified validation logic',
            'PERIOD_MAP_EDIT': 'Changed period mapping',
            'CATEGORY_MAP_EDIT': 'Modified category mapping',
            'TRANSFORMATION_EDIT': 'Changed transformation logic'
        }
    },
    'ARCS': {
        'operational': {
            'RECONCILIATION_PREPARE': 'Prepared reconciliation',
            'RECONCILIATION_CERTIFY': 'Certified reconciliation',
            'TRANSACTION_MATCH_RUN': 'Ran auto-matching',
            'RECONCILIATION_UNCERTIFY': 'Uncertified reconciliation'
        },
        'configuration': {
            'FORMAT_EDIT': 'Modified reconciliation format',
            'PROFILE_EDIT': 'Changed profile assignment',
            'MATCHING_RULE_EDIT': 'Modified matching logic',
            'COMPLIANCE_RULE_EDIT': 'Changed compliance rule'
        }
    }
}


# === SOX MATERIALITY RULES ===

SOX_MATERIALITY_RULES = {
    'always_material': [
        'consolidation_rule_formula_change',
        'business_rule_script_change',
        'approval_hierarchy_modification',
        'access_control_change',
        'validation_rule_modification',
        'chart_of_accounts_structure_change',
        'journal_template_structure_change'
    ],
    'conditionally_material': [
        {
            'rule': 'member_attribute_change',
            'conditions': ['affects_consolidation', 'affects_intercompany', 'changes_data_storage']
        },
        {
            'rule': 'form_layout_change',
            'conditions': ['removes_validation', 'changes_calculation_order', 'affects_data_entry_workflow']
        },
        {
            'rule': 'mapping_rule_change',
            'conditions': ['source_system_change', 'transformation_logic_change', 'affects_financial_statements']
        }
    ],
    'never_material': [
        'cosmetic_formatting',
        'label_translation',
        'descriptive_text',
        'sort_order',
        'display_preferences'
    ]
}


def get_change_type_description(app: str, change_type: str) -> str:
    """Get human-readable description of change type"""
    app_config = CHANGE_TYPE_DEFINITIONS.get(app, {})
    
    # Check operational types
    if change_type in app_config.get('operational', {}):
        return app_config['operational'][change_type]
    
    # Check configuration types
    if change_type in app_config.get('configuration', {}):
        return app_config['configuration'][change_type]
    
    return change_type  # Return as-is if not found


def is_sox_critical_change(app: str, artifact_type: str, changed_fields: List[str]) -> bool:
    """
    Standalone function to check if change is SOX-critical.
    
    Useful for quick checks without full classification.
    """
    critical_artifacts = {
        'consolidation_rule', 'business_rule', 'validation_rule',
        'approval_unit', 'hierarchy', 'mapping_rule', 'access_rule'
    }
    
    if artifact_type.lower().replace(' ', '_') in critical_artifacts:
        return True
    
    critical_patterns = [
        r'(?i)(formula|script|logic).{0,10}(edit|change|update)',
        r'(?i)approval.{0,10}(hierarchy|unit)',
        r'(?i)access.{0,10}(control|security)'
    ]
    
    check_text = f"{artifact_type} {' '.join(changed_fields)}"
    for pattern in critical_patterns:
        if re.search(pattern, check_text):
            return True
    
    return False


# === EXAMPLE USAGE ===

if __name__ == '__main__':
    # Demo classification
    print("EPM Artifact Materiality Filter - Demo")
    print("=" * 60)
    
    classifier = ChangeClassifier()
    
    # Example changes
    test_changes = [
        {
            'application': 'FCCS',
            'artifact_name': 'Period_Feb_2026',
            'artifact_type': 'PERIOD',
            'modified_by': 'system',
            'operation': 'OPEN',
            'change_type': 'STATUS_CHANGE',
            'changed_fields': ['status', 'last_updated']
        },
        {
            'application': 'FCCS',
            'artifact_name': 'Eliminate_IC_Rule',
            'artifact_type': 'consolidation_rule',
            'modified_by': 'john.smith@company.com',
            'operation': 'UPDATE',
            'change_type': 'FORMULA_EDIT',
            'changed_fields': ['formula', 'member_scope', 'last_updated']
        },
        {
            'application': 'PBCS',
            'artifact_name': 'Annual_Budget_Form',
            'artifact_type': 'DATA_FORM',
            'modified_by': 'sarah.jones@company.com',
            'operation': 'UPDATE',
            'change_type': 'DEFINITION_CHANGE',
            'changed_fields': ['layout', 'validation_rules', 'modified_by']
        },
        {
            'application': 'EDM',
            'artifact_name': 'Add_Entity_100',
            'artifact_type': 'REQUEST',
            'modified_by': 'data.admin@company.com',
            'operation': 'APPROVE',
            'change_type': 'REQUEST_APPROVAL',
            'changed_fields': ['status', 'approved_by', 'approved_date', 'last_updated']
        }
    ]
    
    for change in test_changes:
        event = ChangeEvent(
            application=change['application'],
            artifact_name=change['artifact_name'],
            artifact_type=change['artifact_type'],
            modified_by=change['modified_by'],
            modified_date=datetime.now(),
            operation=change['operation'],
            change_type=change['change_type'],
            changed_fields=change['changed_fields']
        )
        
        result = classifier.classify_change(event)
        
        print(f"\n{change['artifact_name']} ({change['application']})")
        print(f"  Operation: {change['operation']}")
        print(f"  Category: {result.category.value}")
        print(f"  Material: {result.material}")
        print(f"  SOX Relevant: {result.sox_relevant}")
        print(f"  Severity: {result.alert_severity.value}")
        print(f"  Reasoning: {'; '.join(result.reasoning)}")
