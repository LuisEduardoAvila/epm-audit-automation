#!/usr/bin/env python3
"""
EPM System Administration Audit Extraction Script

Extracts system-level audit data focused on IT security, infrastructure changes,
and administrative activities across EPM Cloud and OCI resources.

Focus Areas:
- Identity & Access Management (IAM)
- Configuration Management
- Infrastructure Changes
- Security Monitoring
- Compliance Evidence

Usage:
    python extract-epm-admin-audit.py --env prod --type iam --days 1
    python extract-epm-admin-audit.py --env prod --type config --range 2026-02-01 2026-02-26
    python extract-epm-admin-audit.py --env prod --type all --report weekly
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
import csv

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from oci import config as oci_config
    from oci.audit import AuditClient
    from oci.identity import IdentityClient
    from oci.logging import LoggingManagementClient
    from oci.monitoring import MonitoringClient
except ImportError:
    print("Error: OCI Python SDK required. Run: pip install oci")
    sys.exit(1)


class EPMSystemAdminExtractor:
    """Extracts system administration audit data from OCI/EPM"""
    
    # Critical IAM events for security monitoring
    CRITICAL_IAM_EVENTS = {
        'CreateUser', 'DeleteUser', 'UpdateUser',
        'CreateGroup', 'DeleteGroup', 'UpdateGroup',
        'AddUserToGroup', 'RemoveUserFromGroup',
        'CreatePolicy', 'UpdatePolicy', 'DeletePolicy',
        'CreateDynamicGroup', 'UpdateDynamicGroup', 'DeleteDynamicGroup',
        'CreateApiKey', 'DeleteApiKey',
        'CreateAuthToken', 'DeleteAuthToken',
        'CreateCustomerSecretKey', 'DeleteCustomerSecretKey',
        'UpdateAuthToken', 'UpdateCustomerSecretKey',
    }
    
    # Infrastructure events
    CRITICAL_INFRA_EVENTS = {
        'CreateEpminstance', 'UpdateEpminstance', 'DeleteEpminstance',
        'CreateCompartment', 'UpdateCompartment', 'DeleteCompartment',
        'CreateVault', 'UpdateVault', 'DeleteVault',
        'CreateSecret', 'UpdateSecret', 'DeleteSecret',
        'CreateKey', 'UpdateKey', 'DeleteKey',
        'CreateVolume', 'DeleteVolume',
        'CreateVnic', 'DetachVnic', 'DeleteVnic',
        'CreateSecurityList', 'UpdateSecurityList', 'DeleteSecurityList',
        'CreateSecurityRule', 'UpdateSecurityRule', 'DeleteSecurityRule',
        'ChangeSecurityRuleCompartment',
    }
    
    def __init__(self, config_file: Optional[str] = None, profile: str = 'DEFAULT'):
        self.config = oci_config.from_file(config_file, profile)
        
        # Initialize OCI clients
        self.audit_client = AuditClient(self.config)
        self.identity_client = IdentityClient(self.config)
        self.logging_client = LoggingManagementClient(self.config)
        self.monitoring_client = MonitoringClient(self.config)
        
        # Get tenancy info
        self.tenancy_id = self.config.get('tenancy')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def extract_iam_events(self, compartment_id: str, start_time: datetime, 
                           end_time: datetime) -> Dict:
        """
        Extract IAM-related audit events
        
        Security Focus: User lifecycle, privilege changes, access grants
        """
        self.logger.info(f"Extracting IAM events from {start_time} to {end_time}")
        
        events = self._fetch_audit_events(compartment_id, start_time, end_time)
        
        # Categorize IAM events
        iam_events = []
        privilege_changes = []
        access_grants = []
        credential_changes = []
        
        for event in events:
            if event['event_name'] in self.CRITICAL_IAM_EVENTS:
                # Classify the event
                if event['event_name'] in ['CreateUser', 'DeleteUser', 'UpdateUser']:
                    iam_events.append(event)
                    if event['event_name'] == 'CreateUser':
                        self._flag_if_no_ticket(event)
                
                elif event['event_name'] in ['AddUserToGroup', 'RemoveUserFromGroup']:
                    privilege_changes.append(event)
                    self._check_privileged_group(event)
                
                elif event['event_name'] in ['CreatePolicy', 'UpdatePolicy', 'DeletePolicy']:
                    privilege_changes.append(event)
                
                elif event['event_name'] in ['CreateApiKey', 'DeleteApiKey', 
                                             'CreateAuthToken', 'DeleteAuthToken']:
                    credential_changes.append(event)
                    self._check_credential_rotation(event)
        
        # Security analysis
        analysis = self._analyze_iam_security(iam_events, privilege_changes)
        
        return {
            'extraction_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'summary': {
                'total_iam_events': len(iam_events),
                'privilege_changes': len(privilege_changes),
                'credential_changes': len(credential_changes),
                'orphan_accounts_detected': analysis['orphan_accounts'],
                'privileged_changes': analysis['privileged_changes'],
                'unapproved_provisioning': analysis['unapproved'],
                'mfa_violations': analysis['mfa_violations']
            },
            'user_lifecycle': iam_events,
            'privilege_changes': privilege_changes,
            'credential_changes': credential_changes,
            'security_flags': analysis['flags'],
            'extraction_timestamp': datetime.now().isoformat()
        }
    
    def extract_configuration_changes(self, compartment_id: str, start_time: datetime,
                                        end_time: datetime) -> Dict:
        """
        Extract configuration drift and change events
        
        Security Focus: Unauthorized changes, emergency changes, config drift
        """
        self.logger.info(f"Extracting configuration changes from {start_time} to {end_time}")
        
        events = self._fetch_audit_events(compartment_id, start_time, end_time)
        
        config_changes = []
        emergency_changes = []
        infrastructure_changes = []
        
        for event in events:
            # Identify configuration-related events
            if any(keyword in event['event_name'] for keyword in 
                   ['Update', 'Create', 'Delete']):
                
                config_changes.append(event)
                
                # Check for infrastructure events
                if event['event_name'] in self.CRITICAL_INFRA_EVENTS:
                    infrastructure_changes.append(event)
                    self._flag_infrastructure_change(event)
                
                # Identify potential emergency changes (outside maintenance windows)
                event_time = datetime.fromisoformat(event['event_time'].replace('Z', '+00:00'))
                if not self._is_maintenance_window(event_time):
                    emergency_changes.append(event)
        
        # Compare against approved changes (if ServiceNow integration exists)
        unapproved = self._identify_unapproved_changes(config_changes)
        
        return {
            'extraction_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'summary': {
                'total_config_changes': len(config_changes),
                'infrastructure_changes': len(infrastructure_changes),
                'emergency_changes': len(emergency_changes),
                'unapproved_changes': len(unapproved),
                'outside_maintenance': len(emergency_changes)
            },
            'all_changes': config_changes,
            'infrastructure_changes': infrastructure_changes,
            'emergency_flags': emergency_changes,
            'unapproved_changes': unapproved,
            'extraction_timestamp': datetime.now().isoformat()
        }
    
    def extract_user_access_review(self, compartment_id: str) -> Dict:
        """
        Generate user access inventory for periodic review
        
        Security Focus: Access recertification, dormant accounts, privilege creep
        """
        self.logger.info("Extracting user access review data")
        
        access_data = {
            'users': [],
            'service_accounts': [],
            'privileged_users': [],
            'dormant_accounts': [],
            'group_assignments': {}
        }
        
        try:
            # Get all users
            users = self.identity_client.list_users(compartment_id=compartment_id)
            
            for user in users.data:
                user_data = self._enrich_user_data(user, compartment_id)
                
                access_data['users'].append(user_data)
                
                # Categorize
                if user.name.startswith('epm-') or user.name.startswith('svc-'):
                    access_data['service_accounts'].append(user_data)
                
                if self._is_privileged(user, compartment_id):
                    access_data['privileged_users'].append(user_data)
                
                if self._is_dormant(user):
                    access_data['dormant_accounts'].append(user_data)
            
            # Get group memberships
            groups = self.identity_client.list_groups(compartment_id=compartment_id)
            for group in groups.data:
                members = self.identity_client.list_user_group_memberships(
                    compartment_id=compartment_id,
                    group_id=group.id
                )
                access_data['group_assignments'][group.name] = [
                    m.user_id for m in members.data
                ]
            
            # Security analysis
            analysis = self._analyze_access(access_data)
            
            return {
                'extraction_date': datetime.now().isoformat(),
                'summary': {
                    'total_users': len(access_data['users']),
                    'service_accounts': len(access_data['service_accounts']),
                    'privileged_users': len(access_data['privileged_users']),
                    'dormant_accounts': len(access_data['dormant_accounts']),
                    'sod_violations': analysis['sod_violations'],
                    'orphan_accounts': analysis['orphan_accounts'],
                    'accounts_without_mfa': analysis['mfa_gaps']
                },
                'users': access_data['users'],
                'service_accounts': access_data['service_accounts'],
                'privileged_users': access_data['privileged_users'],
                'dormant_accounts': access_data['dormant_accounts'],
                'group_assignments': access_data['group_assignments'],
                'security_flags': analysis['flags'],
                'recommendations': analysis['recommendations'],
                'extraction_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to extract access data: {e}")
            raise
    
    def extract_security_events(self, compartment_id: str, start_time: datetime,
                                  end_time: datetime) -> Dict:
        """
        Extract security-relevant events for monitoring
        
        Security Focus: Failed logins, privilege escalation, data access
        """
        self.logger.info(f"Extracting security events from {start_time} to {end_time}")
        
        events = self._fetch_audit_events(compartment_id, start_time, end_time)
        
        security_events = {
            'failed_logins': [],
            'privilege_escalations': [],
            'data_exports': [],
            'after_hours_access': [],
            'suspicious_patterns': []
        }
        
        for event in events:
            # Failed authentication
            if event['response_status'] == '401' or event['response_status'] == '403':
                security_events['failed_logins'].append(event)
            
            # Privilege changes
            if event['event_name'] in self.CRITICAL_IAM_EVENTS:
                security_events['privilege_escalations'].append(event)
            
            # Data export detection (simplified - customize as needed)
            if 'Export' in event['event_name'] or 'Download' in event['event_name']:
                security_events['data_exports'].append(event)
            
            # After-hours access
            event_time = datetime.fromisoformat(event['event_time'].replace('Z', '+00:00'))
            if self._is_after_hours(event_time):
                security_events['after_hours_access'].append(event)
        
        # Pattern analysis
        patterns = self._analyze_security_patterns(security_events)
        
        return {
            'extraction_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'summary': {
                'failed_login_attempts': len(security_events['failed_logins']),
                'privilege_changes': len(security_events['privilege_escalations']),
                'data_export_events': len(security_events['data_exports']),
                'after_hours_events': len(security_events['after_hours_access']),
                'brute_force_attempts': patterns['brute_force'],
                'impossible_travel': patterns['impossible_travel']
            },
            'events': security_events,
            'patterns': patterns,
            'critical_alerts': self._generate_critical_alerts(security_events),
            'extraction_timestamp': datetime.now().isoformat()
        }
    
    def _fetch_audit_events(self, compartment_id: str, start_time: datetime,
                           end_time: datetime) -> List[Dict]:
        """Internal: Fetch raw audit events from OCI"""
        events = []
        
        try:
            response = self.audit_client.list_events(
                compartment_id=compartment_id,
                start_time=start_time,
                end_time=end_time,
                limit=1000
            )
            
            for event in response.data:
                events.append(self._format_audit_event(event))
            
            # Handle pagination
            while response.has_next_page:
                response = self.audit_client.list_events(
                    compartment_id=compartment_id,
                    start_time=start_time,
                    end_time=end_time,
                    limit=1000,
                    page=response.next_page
                )
                for event in response.data:
                    events.append(self._format_audit_event(event))
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch audit events: {e}")
            raise
        
        return events
    
    def _format_audit_event(self, event) -> Dict:
        """Format OCI audit event to standard structure"""
        return {
            'event_id': event.event_id,
            'event_time': event.event_time.isoformat() if event.event_time else None,
            'event_type': event.event_type,
            'event_name': event.event_name,
            'principal_id': event.principal_id,
            'principal_name': event.principal_name,
            'compartment_id': event.compartment_id,
            'compartment_name': event.compartment_name,
            'source': event.source,
            'target_id': event.target_id,
            'target_name': event.target_name,
            'request_action': event.request_action,
            'response_status': event.response_status,
            'response_status_code': event.response_status_code,
            'client_ip': event.client_hostname,
            'user_agent': event.user_agent,
            'is_critical': (event.event_name in self.CRITICAL_IAM_EVENTS or 
                           event.event_name in self.CRITICAL_INFRA_EVENTS)
        }
    
    def _enrich_user_data(self, user, compartment_id) -> Dict:
        """Enrich user data with membership and activity info"""
        # Get user's group memberships
        try:
            memberships = self.identity_client.list_user_group_memberships(
                compartment_id=compartment_id,
                user_id=user.id
            )
            groups = [m.group_id for m in memberships.data]
        except:
            groups = []
        
        return {
            'user_id': user.id,
            'name': user.name,
            'email': user.email,
            'description': user.description,
            'lifecycle_state': user.lifecycle_state,
            'time_created': user.time_created.isoformat() if user.time_created else None,
            'time_modified': user.time_modified.isoformat() if user.time_modified else None,
            'is_mfa_activated': user.is_mfa_activated,
            'groups': groups,
            'group_count': len(groups),
            'last_login': user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None,
            'capabilities': {
                'can_use_api_keys': user.capabilities.can_use_api_keys if user.capabilities else False,
                'can_use_auth_tokens': user.capabilities.can_use_auth_tokens if user.capabilities else False,
                'can_use_console_password': user.capabilities.can_use_console_password if user.capabilities else False
            }
        }
    
    def _is_privileged(self, user, compartment_id) -> bool:
        """Check if user has admin privileges"""
        try:
            memberships = self.identity_client.list_user_group_memberships(
                compartment_id=compartment_id,
                user_id=user.id
            )
            for m in memberships.data:
                # Check if any group is an admin group
                if 'admin' in str(m).lower():
                    return True
        except:
            pass
        return False
    
    def _is_dormant(self, user, days: int = 90) -> bool:
        """Check if user account is dormant"""
        if not hasattr(user, 'last_login') or not user.last_login:
            # Never logged in - check creation date
            if user.time_created:
                return (datetime.now() - user.time_created.replace(tzinfo=None)).days > days
            return True
        
        return (datetime.now() - user.last_login.replace(tzinfo=None)).days > days
    
    def _is_maintenance_window(self, event_time: datetime) -> bool:
        """Check if time is within approved maintenance windows"""
        # Customize based on your maintenance windows
        # Example: 8PM-6AM on weekends
        hour = event_time.hour
        weekday = event_time.weekday()  # 0=Monday, 6=Sunday
        
        # Weekday after-hours
        if weekday < 5 and (hour >= 20 or hour <= 6):
            return True
        # Weekends
        if weekday >= 5:
            return True
        return False
    
    def _is_after_hours(self, event_time: datetime) -> bool:
        """Check if event occurred outside business hours"""
        hour = event_time.hour
        weekday = event_time.weekday()
        
        # Business hours: 7AM-7PM, Monday-Friday
        if weekday >= 5 or hour < 7 or hour > 19:
            return True
        return False
    
    def _flag_if_no_ticket(self, event: Dict) -> None:
        """Flag event if no approval ticket found"""
        # Placeholder - integrate with ServiceNow/Jira
        pass
    
    def _check_privileged_group(self, event: Dict) -> None:
        """Check if group assignment is to privileged group"""
        # Placeholder - check against privileged group list
        pass
    
    def _check_credential_rotation(self, event: Dict) -> None:
        """Verify credential rotation compliance"""
        # Placeholder - track key ages
        pass
    
    def _flag_infrastructure_change(self, event: Dict) -> None:
        """Flag critical infrastructure changes"""
        self.logger.warning(f"CRITICAL: Infrastructure change detected: {event}")
    
    def _identify_unapproved_changes(self, config_changes: List[Dict]) -> List[Dict]:
        """Compare changes against approved ticket list"""
        # Placeholder - integrate with ServiceNow
        return []
    
    def _analyze_iam_security(self, iam_events: List[Dict], 
                               privilege_changes: List[Dict]) -> Dict:
        """Analyze IAM events for security issues"""
        return {
            'orphan_accounts': 0,
            'privileged_changes': len(privilege_changes),
            'unapproved': 0,
            'mfa_violations': 0,
            'flags': [],
            'recommendations': []
        }
    
    def _analyze_access(self, access_data: Dict) -> Dict:
        """Analyze access data for security findings"""
        return {
            'sod_violations': [],
            'orphan_accounts': [],
            'mfa_gaps': 0,
            'flags': [],
            'recommendations': []
        }
    
    def _analyze_security_patterns(self, security_events: Dict) -> Dict:
        """Analyze events for attack patterns"""
        return {
            'brute_force': 0,
            'impossible_travel': [],
            'privilege_abuse': [],
            'data_exfiltration': []
        }
    
    def _generate_critical_alerts(self, security_events: Dict) -> List[Dict]:
        """Generate alerts for critical events"""
        alerts = []
        
        # Check for brute force
        failed = security_events['failed_logins']
        if len(failed) > 5:
            alerts.append({
                'severity': 'CRITICAL',
                'type': 'BRUTE_FORCE',
                'message': f'{len(failed)} failed login attempts detected'
            })
        
        return alerts


def save_json(data: Dict, filepath: Path):
    """Save data as JSON"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Saved: {filepath}")


def save_csv(data: List[Dict], filepath: Path):
    """Save list of dicts as CSV"""
    if not data:
        return
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Saved: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description='EPM System Administration Audit Extraction'
    )
    parser.add_argument('--compartment', required=True,
                       help='OCI Compartment OCID')
    parser.add_argument('--type', required=True,
                       choices=['iam', 'config', 'access', 'security', 'all'],
                       help='Type of audit extraction')
    parser.add_argument('--days', type=int, default=1,
                       help='Days to look back (default: 1)')
    parser.add_argument('--start', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', help='End date (YYYY-MM-DD)')
    parser.add_argument('--config-file', help='OCI config file')
    parser.add_argument('--profile', default='DEFAULT',
                       help='OCI config profile')
    parser.add_argument('--output', default='./outputs/admin',
                       help='Output directory')
    
    args = parser.parse_args()
    
    # Initialize extractor
    extractor = EPMSystemAdminExtractor(args.config_file, args.profile)
    
    # Create output directory
    output_dir = Path(args.output) / datetime.now().strftime('%Y-%m-%d')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"EPM Admin Audit Extraction")
    print(f"Type: {args.type.upper()}")
    print(f"Compartment: {args.compartment}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}\n")
    
    # Determine time range
    if args.start and args.end:
        start_time = datetime.strptime(args.start, '%Y-%m-%d')
        end_time = datetime.strptime(args.end, '%Y-%m-%d') + timedelta(days=1)
    else:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=args.days)
    
    # Run extractions
    timestamp = datetime.now().strftime('%Y%m%d')
    
    if args.type in ['iam', 'all']:
        print("\n--- Extracting IAM Events ---")
        iam_data = extractor.extract_iam_events(args.compartment, start_time, end_time)
        save_json(iam_data, output_dir / f'iam_events_{timestamp}.json')
        if iam_data.get('user_lifecycle'):
            save_csv(iam_data['user_lifecycle'], output_dir / f'iam_lifecycle_{timestamp}.csv')
    
    if args.type in ['config', 'all']:
        print("\n--- Extracting Configuration Changes ---")
        config_data = extractor.extract_configuration_changes(
            args.compartment, start_time, end_time
        )
        save_json(config_data, output_dir / f'config_changes_{timestamp}.json')
    
    if args.type in ['access', 'all']:
        print("\n--- Extracting User Access Review ---")
        access_data = extractor.extract_user_access_review(args.compartment)
        save_json(access_data, output_dir / f'access_review_{timestamp}.json')
    
    if args.type in ['security', 'all']:
        print("\n--- Extracting Security Events ---")
        security_data = extractor.extract_security_events(
            args.compartment, start_time, end_time
        )
        save_json(security_data, output_dir / f'security_events_{timestamp}.json')
    
    print(f"\n{'='*60}")
    print("Extraction Complete")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
