"""
OCI IAM/Identity Client for EPM Audit CLI.

Wraps OCI IdentityClient for user, group, and membership queries.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from epm_audit_cli.exceptions import EPMValidationError, EPMConnectionError

logger = logging.getLogger(__name__)


class IAMClient:
    """
    OCI Identity and Access Management client.
    
    Provides access to users, groups, and memberships for SOX access reviews.
    """
    
    # Privileged group patterns
    PRIVILEGED_GROUPS = {
        'Administrators', 'IDCSAdministrators', 'SecurityAdmins',
        'EPMAdministrators', 'FCAdministrators', 'PBCSAdministrators',
    }
    
    # Service account patterns
    SERVICE_ACCOUNT_PATTERNS = ('epm-', 'svc-', 'automation-', 'service-')
    
    # Dormant threshold (days)
    DEFAULT_DORMANT_DAYS = 90
    
    def __init__(self, config: Optional[Dict] = None, profile: str = 'DEFAULT'):
        """
        Initialize IAM client.
        
        Args:
            config: OCI config dict (if None, loads from ~/.oci/config)
            profile: OCI config profile name
        """
        self._check_oci_available()
        
        if config is None:
            from oci import config as oci_config
            config = oci_config.from_file(profile=profile)
        
        self.config = config
        self.tenancy_id = config.get('tenancy')
        
        from oci.identity import IdentityClient
        self.client = IdentityClient(config)
    
    @staticmethod
    def _check_oci_available() -> bool:
        """Check if OCI SDK is available."""
        try:
            import oci
            return True
        except ImportError:
            raise EPMConnectionError(
                "OCI SDK not installed",
                suggestion="Install with: pip install oci",
            )
    
    def list_users(self, compartment_id: Optional[str] = None) -> List[Dict]:
        """
        List all users in compartment.
        
        Args:
            compartment_id: Compartment OCID (defaults to tenancy)
            
        Returns:
            List of user dicts with id, name, email, last_login, status
        """
        compartment_id = compartment_id or self.tenancy_id
        
        try:
            response = self.client.list_users(compartment_id=compartment_id)
            users = []
            
            for user in response.data:
                user_data = {
                    'id': user.id,
                    'name': user.name,
                    'display_name': user.display_name,
                    'email': user.email,
                    'description': getattr(user, 'description', ''),
                    'time_created': user.time_created.isoformat() if user.time_created else None,
                    'lifecycle_state': user.lifecycle_state,
                    'is_service_account': self._is_service_account_name(user.name),
                }
                
                # Try to get last login time
                user_data['last_login'] = self._get_last_login(user.id)
                user_data['dormant_days'] = self._calculate_dormant_days(user_data['last_login'])
                
                users.append(user_data)
            
            logger.info(f"Retrieved {len(users)} users from compartment {compartment_id[:20]}...")
            return users
            
        except Exception as e:
            raise EPMConnectionError(
                f"Failed to list users: {str(e)}",
                suggestion="Check OCI config and compartment OCID",
            )
    
    def list_groups(self, compartment_id: Optional[str] = None) -> List[Dict]:
        """
        List all groups in compartment.
        
        Args:
            compartment_id: Compartment OCID (defaults to tenancy)
            
        Returns:
            List of group dicts with id, name, member_count, is_privileged
        """
        compartment_id = compartment_id or self.tenancy_id
        
        try:
            response = self.client.list_groups(compartment_id=compartment_id)
            groups = []
            
            for group in response.data:
                group_data = {
                    'id': group.id,
                    'name': group.name,
                    'display_name': getattr(group, 'display_name', group.name),
                    'description': getattr(group, 'description', ''),
                    'time_created': group.time_created.isoformat() if group.time_created else None,
                    'lifecycle_state': group.lifecycle_state,
                    'is_privileged': self._is_privileged_group(group.name),
                }
                
                # Get member count
                try:
                    members = self.client.list_user_group_memberships(
                        compartment_id=compartment_id,
                        group_id=group.id
                    )
                    group_data['member_count'] = len(members.data)
                except:
                    group_data['member_count'] = 'N/A'
                
                groups.append(group_data)
            
            logger.info(f"Retrieved {len(groups)} groups from compartment {compartment_id[:20]}...")
            return groups
            
        except Exception as e:
            raise EPMConnectionError(
                f"Failed to list groups: {str(e)}",
                suggestion="Check OCI config and compartment OCID",
            )
    
    def get_group_memberships(self, compartment_id: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get user-group membership mapping.
        
        Args:
            compartment_id: Compartment OCID (defaults to tenancy)
            
        Returns:
            Dict mapping group name to list of user IDs
        """
        compartment_id = compartment_id or self.tenancy_id
        memberships = {}
        
        try:
            groups = self.client.list_groups(compartment_id=compartment_id)
            
            for group in groups.data:
                try:
                    members = self.client.list_user_group_memberships(
                        compartment_id=compartment_id,
                        group_id=group.id
                    )
                    memberships[group.name] = [m.user_id for m in members.data]
                except:
                    memberships[group.name] = []
            
            logger.info(f"Retrieved memberships for {len(memberships)} groups")
            return memberships
            
        except Exception as e:
            raise EPMConnectionError(
                f"Failed to get group memberships: {str(e)}",
                suggestion="Check OCI config and compartment OCID",
            )
    
    def get_user_memberships(self, user_id: str, compartment_id: Optional[str] = None) -> List[str]:
        """
        Get groups a user belongs to.
        
        Args:
            user_id: User OCID
            compartment_id: Compartment OCID (defaults to tenancy)
            
        Returns:
            List of group OCIDs
        """
        compartment_id = compartment_id or self.tenancy_id
        
        try:
            memberships = self.client.list_user_group_memberships(
                compartment_id=compartment_id,
                user_id=user_id
            )
            return [m.group_id for m in memberships.data]
        except Exception as e:
            logger.warning(f"Failed to get memberships for user {user_id}: {e}")
            return []
    
    def get_access_review(self, compartment_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive access review for SOX audit.
        
        Args:
            compartment_id: Compartment OCID (defaults to tenancy)
            
        Returns:
            Dict with users, groups, memberships, and security analysis
        """
        compartment_id = compartment_id or self.tenancy_id
        
        logger.info(f"Starting access review for compartment {compartment_id[:20]}...")
        
        # Get users and groups
        users = self.list_users(compartment_id)
        groups = self.list_groups(compartment_id)
        
        # Build membership map
        memberships = self.get_group_memberships(compartment_id)
        
        # Categorize users
        service_accounts = [u for u in users if u['is_service_account']]
        human_users = [u for u in users if not u['is_service_account']]
        dormant_accounts = [u for u in users if u['dormant_days'] is not None and u['dormant_days'] > self.DEFAULT_DORMANT_DAYS]
        privileged_users = []
        orphan_accounts = []
        
        # Find privileged and orphan users
        user_group_map = {}  # user_id -> group names
        for group_name, user_ids in memberships.items():
            for user_id in user_ids:
                if user_id not in user_group_map:
                    user_group_map[user_id] = []
                user_group_map[user_id].append(group_name)
        
        for user in users:
            user_groups = user_group_map.get(user['id'], [])
            
            # Check if privileged
            if any(self._is_privileged_group(g) for g in user_groups):
                user['privileged_groups'] = user_groups
                privileged_users.append(user)
            
            # Check if orphan (no group memberships)
            if not user_groups:
                orphan_accounts.append(user)
        
        # Security analysis
        analysis = self._analyze_access(users, groups, memberships, privileged_users, dormant_accounts, orphan_accounts)
        
        return {
            'extraction_date': datetime.now().isoformat(),
            'compartment_id': compartment_id,
            'summary': {
                'total_users': len(users),
                'human_users': len(human_users),
                'service_accounts': len(service_accounts),
                'privileged_users': len(privileged_users),
                'dormant_accounts': len(dormant_accounts),
                'orphan_accounts': len(orphan_accounts),
                'total_groups': len(groups),
                'privileged_groups': len([g for g in groups if g['is_privileged']]),
                'sod_violations': analysis['sod_violations'],
            },
            'users': users,
            'groups': groups,
            'memberships': memberships,
            'service_accounts': service_accounts,
            'privileged_users': privileged_users,
            'dormant_accounts': dormant_accounts,
            'orphan_accounts': orphan_accounts,
            'security_flags': analysis['flags'],
            'recommendations': analysis['recommendations'],
        }
    
    def _is_service_account_name(self, name: str) -> bool:
        """Check if name matches service account pattern."""
        return any(name.lower().startswith(p) for p in self.SERVICE_ACCOUNT_PATTERNS)
    
    def _is_privileged_group(self, group_name: str) -> bool:
        """Check if group is a privileged/admin group."""
        group_lower = group_name.lower()
        return any(
            admin in group_lower for admin in ['admin', 'administrator', 'security', 'privilege']
        ) or group_name in self.PRIVILEGED_GROUPS
    
    def _get_last_login(self, user_id: str) -> Optional[str]:
        """
        Get last login timestamp for user.
        
        Note: OCI IAM doesn't store last login directly.
        This would require querying audit events.
        """
        # Placeholder - would need to query audit events
        # For now, return None (dormant detection would need audit logs)
        return None
    
    def _calculate_dormant_days(self, last_login: Optional[str]) -> Optional[int]:
        """Calculate days since last login."""
        if last_login is None:
            return None
        
        try:
            last = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
            return (datetime.now(last.tzinfo) - last).days
        except:
            return None
    
    def _analyze_access(
        self,
        users: List[Dict],
        groups: List[Dict],
        memberships: Dict[str, List[str]],
        privileged_users: List[Dict],
        dormant_accounts: List[Dict],
        orphan_accounts: List[Dict]
    ) -> Dict:
        """
        Analyze access data for security issues.
        
        Returns:
            Dict with sod_violations, flags, recommendations
        """
        flags = []
        recommendations = []
        
        # Flag high number of privileged users
        if len(privileged_users) > len(users) * 0.2:  # >20% privileged
            flags.append({
                'severity': 'HIGH',
                'type': 'EXCESSIVE_PRIVILEGES',
                'message': f"{len(privileged_users)} privileged users ({len(privileged_users)/len(users)*100:.1f}% of total)",
                'remediation': 'Review privileged group memberships and apply least privilege',
            })
        
        # Flag dormant accounts
        if dormant_accounts:
            flags.append({
                'severity': 'MEDIUM',
                'type': 'DORMANT_ACCOUNTS',
                'message': f"{len(dormant_accounts)} accounts with no recent login",
                'remediation': 'Review dormant accounts for deactivation',
            })
        
        # Flag orphan accounts
        if orphan_accounts:
            flags.append({
                'severity': 'MEDIUM',
                'type': 'ORPHAN_ACCOUNTS',
                'message': f"{len(orphan_accounts)} accounts with no group memberships",
                'remediation': 'Assign appropriate groups or deactivate',
            })
        
        # SoD violation detection (simplified)
        # In practice, this would check for conflicting role combinations
        sod_violations = 0
        user_groups = {}
        for group_name, user_ids in memberships.items():
            for user_id in user_ids:
                if user_id not in user_groups:
                    user_groups[user_id] = set()
                user_groups[user_id].add(group_name)
        
        # Check for SoD conflicts (example: Admin + Finance)
        sod_conflicts = [
            {'Admin', 'Finance'},
            {'Security', 'Audit'},
            {'Development', 'Production'},
        ]
        
        for user_id, group_set in user_groups.items():
            for conflict_set in sod_conflicts:
                if conflict_set.issubset(group_set):
                    sod_violations += 1
                    flags.append({
                        'severity': 'HIGH',
                        'type': 'SOD_VIOLATION',
                        'message': f"User {user_id[:30]}... has conflicting groups: {conflict_set}",
                        'remediation': 'Review and resolve segregation of duties conflict',
                    })
        
        # Generate recommendations
        if len(privileged_users) > 10:
            recommendations.append("Implement privileged access management (PAM)")
        
        if dormant_accounts:
            recommendations.append("Implement automated dormant account review process")
        
        if orphan_accounts:
            recommendations.append("Review orphan accounts and assign appropriate groups")
        
        if sod_violations > 0:
            recommendations.append("Implement SoD monitoring and enforcement")
        
        return {
            'sod_violations': sod_violations,
            'flags': flags,
            'recommendations': recommendations,
        }