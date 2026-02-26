#!/usr/bin/env python3
"""
OCI Audit Log Extraction Script

Extracts Oracle Cloud Infrastructure audit logs for IAM changes,
API calls, and resource modifications relevant to SOX compliance.

Usage:
    python extract-oci-audit.py --compartment ocid1.compartment.xxx --days 1
    python extract-oci-audit.py --compartment ocid1.compartment.xxx --start 2026-02-01 --end 2026-02-26
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import csv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from oci import config as oci_config
    from oci.audit import AuditClient
    from oci.identity import IdentityClient
    from oci.exceptions import ServiceError
except ImportError:
    print("Error: OCI Python SDK required. Run: pip install oci")
    print("Documentation: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/pythonsdk.htm")
    sys.exit(1)


class OCIAuditExtractor:
    """Extracts audit logs from OCI"""
    
    # SOX-relevant event types to filter for
    SOX_CRITICAL_EVENTS = {
        'CreateUser', 'UpdateUser', 'DeleteUser',
        'CreateGroup', 'UpdateGroup', 'DeleteGroup',
        'AddUserToGroup', 'RemoveUserFromGroup',
        'CreatePolicy', 'UpdatePolicy', 'DeletePolicy',
        'CreateCompartment', 'UpdateCompartment', 'DeleteCompartment',
        'CreateApiKey', 'DeleteApiKey',
        'CreateAuthToken', 'DeleteAuthToken',
        'CreateCustomerSecretKey', 'DeleteCustomerSecretKey',
        'CreateEpminstance', 'UpdateEpminstance', 'DeleteEpminstance',
        'CreateVault', 'UpdateVault', 'DeleteVault',
        'CreateSecret', 'UpdateSecret', 'DeleteSecret'
    }
    
    def __init__(self, config_file: Optional[str] = None, profile: str = 'DEFAULT'):
        self.config = oci_config.from_file(config_file, profile)
        self.audit_client = AuditClient(self.config)
        self.identity_client = IdentityClient(self.config)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def get_audit_events(self, compartment_id: str, start_time: datetime, 
                        end_time: datetime, filter_sox: bool = True) -> List[Dict]:
        """
        Extract audit events for compartment and time range
        
        SOX Relevance: All IAM and infrastructure changes
        """
        self.logger.info(f"Fetching audit events from {start_time} to {end_time}")
        
        events = []
        
        try:
            # OCI audit events are paginated
            response = self.audit_client.list_events(
                compartment_id=compartment_id,
                start_time=start_time,
                end_time=end_time,
                limit=1000  # Max per request
            )
            
            for event in response.data:
                event_data = {
                    'event_id': event.event_id,
                    'event_time': event.event_time.isoformat() if event.event_time else None,
                    'event_type': event.event_type,
                    'event_name': event.event_name,
                    'source': event.source,
                    'actor_principal_id': event.principal_id,
                    'actor_principal_name': self._get_principal_name(event.principal_id),
                    'compartment_id': event.compartment_id,
                    'compartment_name': self._get_compartment_name(event.compartment_id),
                    'target_resource_id': event.target_id,
                    'target_resource_name': event.target_name,
                    'target_resource_type': event.target_resource_type,
                    'request_action': event.request_action,
                    'response_status': event.response_status,
                    'response_status_code': event.response_status_code,
                    'client_ip': event.client_hostname,
                    'user_agent': event.user_agent,
                    'request_headers': json.dumps(dict(event.request_headers)) if event.request_headers else None,
                    'request_payload': json.dumps(dict(event.request_resource)) if event.request_resource else None,
                    'response_payload': json.dumps(dict(event.response_resource)) if event.response_resource else None,
                    'sox_critical': event.event_name in self.SOX_CRITICAL_EVENTS,
                    'extraction_timestamp': datetime.now().isoformat()
                }
                
                # Filter to SOX-critical events if requested
                if filter_sox and event.event_name not in self.SOX_CRITICAL_EVENTS:
                    continue
                
                events.append(event_data)
            
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
                    event_data = {
                        'event_id': event.event_id,
                        'event_time': event.event_time.isoformat() if event.event_time else None,
                        'event_type': event.event_type,
                        'event_name': event.event_name,
                        'source': event.source,
                        'actor_principal_id': event.principal_id,
                        'actor_principal_name': self._get_principal_name(event.principal_id),
                        'compartment_id': event.compartment_id,
                        'compartment_name': self._get_compartment_name(event.compartment_id),
                        'target_resource_id': event.target_id,
                        'target_resource_name': event.target_name,
                        'target_resource_type': event.target_resource_type,
                        'request_action': event.request_action,
                        'response_status': event.response_status,
                        'response_status_code': event.response_status_code,
                        'client_ip': event.client_hostname,
                        'user_agent': event.user_agent,
                        'sox_critical': event.event_name in self.SOX_CRITICAL_EVENTS,
                        'extraction_timestamp': datetime.now().isoformat()
                    }
                    
                    if filter_sox and event.event_name not in self.SOX_CRITICAL_EVENTS:
                        continue
                    
                    events.append(event_data)
            
            self.logger.info(f"Extracted {len(events)} audit events")
            
        except ServiceError as e:
            self.logger.error(f"OCI API error: {e.message}")
            raise
        
        return events
    
    def get_user_access_summary(self, compartment_id: str) -> Dict:
        """
        Get current user access state
        
        SOX Relevance: Snapshot of who has access to what
        """
        self.logger.info("Fetching user access summary")
        
        users = []
        groups = []
        policies = []
        
        try:
            # Get users
            user_response = self.identity_client.list_users(compartment_id=compartment_id)
            for user in user_response.data:
                user_data = {
                    'user_id': user.id,
                    'user_name': user.name,
                    'description': user.description,
                    'email': user.email,
                    'lifecycle_state': user.lifecycle_state,
                    'created_by': user.created_by,
                    'time_created': user.time_created.isoformat() if user.time_created else None,
                    'time_modified': user.time_modified.isoformat() if user.time_modified else None,
                    'is_mfa_activated': user.is_mfa_activated,
                    'capabilities': {
                        'can_use_api_keys': user.capabilities.can_use_api_keys if user.capabilities else None,
                        'can_use_auth_tokens': user.capabilities.can_use_auth_tokens if user.capabilities else None,
                        'can_use_console_password': user.capabilities.can_use_console_password if user.capabilities else None,
                        'can_use_customer_secret_keys': user.capabilities.can_use_customer_secret_keys if user.capabilities else None
                    },
                    'extraction_timestamp': datetime.now().isoformat()
                }
                users.append(user_data)
            
            # Get groups
            group_response = self.identity_client.list_groups(compartment_id=compartment_id)
            for group in group_response.data:
                # Get group members
                members = []
                try:
                    member_response = self.identity_client.list_user_group_memberships(
                        compartment_id=compartment_id,
                        group_id=group.id
                    )
                    for membership in member_response.data:
                        members.append({
                            'user_id': membership.user_id,
                            'membership_id': membership.id,
                            'time_created': membership.time_created.isoformat() if membership.time_created else None
                        })
                except ServiceError:
                    pass  # Group may have no members
                
                group_data = {
                    'group_id': group.id,
                    'group_name': group.name,
                    'description': group.description,
                    'member_count': len(members),
                    'members': members,
                    'lifecycle_state': group.lifecycle_state,
                    'time_created': group.time_created.isoformat() if group.time_created else None,
                    'extraction_timestamp': datetime.now().isoformat()
                }
                groups.append(group_data)
            
            # Get policies
            policy_response = self.identity_client.list_policies(compartment_id=compartment_id)
            for policy in policy_response.data:
                policy_data = {
                    'policy_id': policy.id,
                    'policy_name': policy.name,
                    'description': policy.description,
                    'lifecycle_state': policy.lifecycle_state,
                    'statements': policy.statements,
                    'time_created': policy.time_created.isoformat() if policy.time_created else None,
                    'time_modified': policy.time_modified.isoformat() if policy.time_modified else None,
                    'extraction_timestamp': datetime.now().isoformat()
                }
                policies.append(policy_data)
            
        except ServiceError as e:
            self.logger.error(f"OCI API error: {e.message}")
            raise
        
        return {
            'user_count': len(users),
            'group_count': len(groups),
            'policy_count': len(policies),
            'users': users,
            'groups': groups,
            'policies': policies,
            'extraction_timestamp': datetime.now().isoformat()
        }
    
    def _get_principal_name(self, principal_id: str) -> Optional[str]:
        """Lookup principal name from ID"""
        # Simplified - in production, cache user/group lookups
        return principal_id  # Return ID if lookup fails
    
    def _get_compartment_name(self, compartment_id: str) -> Optional[str]:
        """Lookup compartment name from ID"""
        # Simplified - in production, cache compartment lookups
        return compartment_id  # Return ID if lookup fails


def save_json(data: Dict, filepath: Path):
    """Save data as JSON file"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Saved: {filepath}")


def save_csv(data: List[Dict], filepath: Path):
    """Save list of dicts as CSV"""
    if not data:
        print(f"No data to save to {filepath}")
        return
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Saved: {filepath}")


def main():
    parser = argparse.ArgumentParser(description='OCI Audit Log Extraction')
    parser.add_argument('--compartment', required=True, 
                       help='Compartment OCID (usually root or EPM compartment)')
    parser.add_argument('--days', type=int, default=1,
                       help='Number of days to look back (default: 1)')
    parser.add_argument('--start', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', help='End date (YYYY-MM-DD)')
    parser.add_argument('--config', help='OCI config file path (default: ~/.oci/config)')
    parser.add_argument('--profile', default='DEFAULT', help='OCI config profile (default: DEFAULT)')
    parser.add_argument('--output', default='./outputs/oci', help='Output directory')
    parser.add_argument('--sox-only', action='store_true',
                       help='Only extract SOX-critical events')
    parser.add_argument('--include-access-summary', action='store_true',
                       help='Include current user/group snapshot')
    
    args = parser.parse_args()
    
    # Initialize extractor
    extractor = OCIAuditExtractor(args.config, args.profile)
    
    # Create output directory
    output_dir = Path(args.output) / datetime.now().strftime('%Y-%m-%d')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"OCI Audit Extraction")
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
    
    print(f"Time Range: {start_time.isoformat()} to {end_time.isoformat()}")
    
    # Extract audit events
    print("\n--- Extracting Audit Events ---")
    events = extractor.get_audit_events(
        compartment_id=args.compartment,
        start_time=start_time,
        end_time=end_time,
        filter_sox=args.sox_only
    )
    
    if events:
        save_json({'events': events}, output_dir / f'audit_events_{start_time.strftime("%Y%m%d")}_{end_time.strftime("%Y%m%d")}.json')
        save_csv(events, output_dir / f'audit_events_{start_time.strftime("%Y%m%d")}_{end_time.strftime("%Y%m%d")}.csv')
    else:
        print("No audit events found for the specified period")
    
    # Extract access summary if requested
    if args.include_access_summary:
        print("\n--- Extracting Access Summary ---")
        access_summary = extractor.get_user_access_summary(args.compartment)
        save_json(access_summary, output_dir / f'access_summary_{datetime.now().strftime("%Y%m%d")}.json')
    
    print(f"\n{'='*60}")
    print("Extraction Complete")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
