#!/usr/bin/env python3
"""
EPM Audit Automation - Integrated Example

Shows how credential management integrates with artifact extraction
for a complete audit workflow.

Usage:
    python integrated_audit_example.py --app fccs_prod --days 7
"""

import argparse
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent))

from credential_manager import CredentialManager
from extract_artifact_changes import EPMArtifactExtractor


class EPMAuditOrchestrator:
    """
    Orchestrates complete audit workflow with credential management
    """
    
    def __init__(self, config_path: str = 'config/applications.yaml'):
        """
        Initialize orchestrator
        
        Loads configuration and initializes credential manager
        """
        self.config_path = Path(config_path)
        
        # Initialize credential manager
        self.creds = CredentialManager(
            str(self.config_path),
            backend_type='auto'  # Auto-detect: OCI Vault → Keyring → Env
        )
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def get_app_config(self, app_id: str) -> dict:
        """Get full application configuration"""
        return self.creds.get_application(app_id)
    
    def audit_app(self, app_id: str, days: int = 1) -> dict:
        """
        Run complete audit for single application
        
        Steps:
        1. Get OAuth token
        2. Generate artifact report
        3. Classify changes
        4. Check SOX compliance
        5. Return structured results
        """
        self.logger.info(f"="*60)
        self.logger.info(f"Auditing: {app_id}")
        self.logger.info(f"="*60)
        
        try:
            # Step 1: Get authentication
            self.logger.info("Authenticating...")
            token = self.creds.get_oauth_token(app_id)
            app_config = self.creds.get_application(app_id)
            self.logger.info(f"✓ Authenticated as: {app_config['name']}")
            
            # Step 2: Generate report
            self.logger.info("Generating artifact report...")
            
            # Note: In production, this would:
            # 1. Call REST API to generate CSV
            # 2. Download CSV from Outbox
            # 3. Process and classify
            
            # For demo, simulate report generation
            report_data = self._simulate_artifact_report(app_id, days)
            
            # Step 3: Classify changes
            self.logger.info("Classifying changes...")
            classified = self._classify_changes(report_data)
            
            # Step 4: SOX compliance check
            sox_check = self._check_sox_compliance(app_id, classified)
            
            # Step 5: Build result
            result = {
                'app_id': app_id,
                'app_name': app_config['name'],
                'environment': app_config['environment'],
                'audit_timestamp': datetime.utcnow().isoformat(),
                'period_days': days,
                'authentication': 'success',
                'summary': {
                    'total_changes': len(report_data),
                    'material_changes': len(classified['material']),
                    'sox_critical': len(classified['sox_critical']),
                    'requires_action': len(classified['requires_action'])
                },
                'changes': {
                    'material': classified['material'][:10],  # Top 10
                    'sox_critical': classified['sox_critical']
                },
                'sox_compliance': sox_check
            }
            
            self.logger.info(f"✓ Audit complete")
            self.logger.info(f"  Total changes: {result['summary']['total_changes']}")
            self.logger.info(f"  Material: {result['summary']['material_changes']}")
            self.logger.info(f"  SOX Critical: {result['summary']['sox_critical']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"✗ Audit failed: {e}")
            return {
                'app_id': app_id,
                'audit_timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def audit_environment(self, environment: str, days: int = 1) -> list:
        """
        Audit all applications in an environment
        
        Uses shared OAuth token for efficiency within environment
        """
        self.logger.info(f"Auditing all {environment} applications...")
        
        # Get all apps in environment
        app_ids = self.creds.get_applications_by_environment(environment)
        
        results = []
        for app_id in app_ids:
            result = self.audit_app(app_id, days)
            results.append(result)
        
        return results
    
    def audit_sox_critical(self, days: int = 1) -> list:
        """
        Audit only SOX-critical applications
        """
        self.logger.info("Auditing SOX-critical applications...")
        
        # Get all apps
        all_apps = self.creds.list_applications()
        
        # Filter to SOX-relevant
        sox_apps = [
            app['id'] for app in all_apps
            if self.creds.is_sox_relevant(app['id'])
        ]
        
        results = []
        for app_id in sox_apps:
            result = self.audit_app(app_id, days)
            results.append(result)
        
        return results
    
    def generate_environment_summary(self, environment: str) -> dict:
        """
        Generate summary dashboard for environment
        """
        app_ids = self.creds.get_applications_by_environment(environment)
        
        summary = {
            'environment': environment,
            'timestamp': datetime.utcnow().isoformat(),
            'applications': {
                'total': len(app_ids),
                'sox_relevant': sum(
                    1 for app in app_ids
                    if self.creds.is_sox_relevant(app)
                )
            },
            'apps': []
        }
        
        for app_id in app_ids:
            app = self.creds.get_application(app_id)
            summary['apps'].append({
                'id': app_id,
                'name': app['name'],
                'type': app['type'],
                'criticality': app['metadata'].get('criticality', 'medium'),
                'sox_relevant': app['metadata'].get('sox_relevant', False)
            })
        
        return summary
    
    def _simulate_artifact_report(self, app_id: str, days: int) -> list:
        """
        Simulate artifact report data
        
        In production, this would call the actual REST API
        """
        # This is a placeholder - in production this would:
        # 1. POST to /applicationsnapshots/reports/artifactupdates
        # 2. Download CSV from Outbox
        # 3. Parse CSV into structured data
        
        return [
            {
                'artifact_name': 'Eliminate_IC',
                'artifact_type': 'CONSOLIDATION_RULE',
                'modified_by': 'john.smith',
                'modified_date': (datetime.utcnow() - timedelta(days=2)).isoformat(),
                'change_summary': 'Formula updated'
            },
            {
                'artifact_name': 'Actual_Vs_Budget',
                'artifact_type': 'DATA_FORM',
                'modified_by': 'jane.doe',
                'modified_date': (datetime.utcnow() - timedelta(days=5)).isoformat(),
                'change_summary': 'Validation rule added'
            },
            {
                'artifact_name': 'Feb-26',
                'artifact_type': 'PERIOD_STATUS',
                'modified_by': 'SYSTEM',
                'modified_date': datetime.utcnow().isoformat(),
                'change_summary': 'Period opened'
            }
        ]
    
    def _classify_changes(self, changes: list) -> dict:
        """Classify changes using the materiality filter"""
        
        # Use the same classification logic from extract_artifact_changes.py
        operational_types = {
            'PERIOD', 'PERIOD_STATUS', 'JOB', 'EXECUTION',
            'JOURNAL_POSTING', 'FORM_SAVE', 'APPROVAL'
        }
        
        configuration_types = {
            'CONSOLIDATION_RULE', 'BUSINESS_RULE', 'DATA_FORM',
            'DIMENSION', 'ATTRIBUTE', 'SMART_LIST'
        }
        
        classified = {
            'all': changes,
            'material': [],
            'operational': [],
            'sox_critical': [],
            'requires_action': []
        }
        
        for change in changes:
            a_type = change.get('artifact_type', '').upper()
            
            if any(t in a_type for t in operational_types):
                classified['operational'].append(change)
            elif any(t in a_type for t in configuration_types):
                classified['material'].append(change)
                
                # Check SOX critical
                if 'CONSOLIDATION' in a_type or 'ELIMINATION' in a_type:
                    classified['sox_critical'].append(change)
                    classified['requires_action'].append(change)
            else:
                classified['material'].append(change)  # Assume material if unknown
        
        return classified
    
    def _check_sox_compliance(self, app_id: str, classified: dict) -> dict:
        """Check SOX compliance for application"""
        
        if not self.creds.is_sox_relevant(app_id):
            return {
                'sox_relevant': False,
                'status': 'N/A'
            }
        
        checks = {
            'sox_relevant': True,
            'status': 'COMPLIANT',
            'checks': {
                'no_unapproved_changes': len(classified['sox_critical']) == 0,
                'all_changes_documented': True,  # Would verify in production
                'audit_trail_complete': True   # Would verify in production
            }
        }
        
        if classified['sox_critical']:
            checks['status'] = 'ATTENTION_REQUIRED'
        
        return checks
    
    def save_results(self, results: list, output_dir: Path):
        """Save audit results to files"""
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save full results
        results_file = output_dir / f'audit_results_{timestamp}.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        self.logger.info(f"✓ Results saved: {results_file}")
        
        # Generate summary report
        summary = self._generate_summary_report(results)
        summary_file = output_dir / f'audit_summary_{timestamp}.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        self.logger.info(f"✓ Summary saved: {summary_file}")
        
        # CSV for Excel
        csv_file = output_dir / f'audit_summary_{timestamp}.csv'
        self._save_csv_summary(results, csv_file)
        self.logger.info(f"✓ CSV saved: {csv_file}")
    
    def _generate_summary_report(self, results: list) -> dict:
        """Generate high-level summary"""
        total_apps = len(results)
        errors = sum(1 for r in results if 'error' in r)
        total_changes = sum(r.get('summary', {}).get('total_changes', 0) for r in results)
        sox_critical = sum(r.get('summary', {}).get('sox_critical', 0) for r in results)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'applications_audited': total_apps,
            'errors': errors,
            'total_changes_detected': total_changes,
            'sox_critical_changes': sox_critical,
            'requires_attention': sox_critical > 0
        }
    
    def _save_csv_summary(self, results: list, csv_path: Path):
        """Save summary as CSV"""
        import csv
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Application', 'Environment', 'Total Changes',
                'Material Changes', 'SOX Critical', 'Status'
            ])
            
            for result in results:
                if 'error' not in result:
                    writer.writerow([
                        result['app_name'],
                        result['environment'],
                        result['summary']['total_changes'],
                        result['summary']['material_changes'],
                        result['summary']['sox_critical'],
                        'OK' if result['summary']['sox_critical'] == 0 else 'ATTENTION'
                    ])


def main():
    parser = argparse.ArgumentParser(
        description='Integrated EPM Audit Example'
    )
    parser.add_argument('--config', default='config/applications.yaml',
                       help='Configuration file path')
    parser.add_argument('--app', help='Specific application ID to audit')
    parser.add_argument('--env', help='Audit all apps in environment')
    parser.add_argument('--sox-only', action='store_true',
                       help='Audit only SOX-relevant apps')
    parser.add_argument('--days', type=int, default=1,
                       help='Number of days to look back')
    parser.add_argument('--output', default='./outputs/audit',
                       help='Output directory')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    print("Initializing audit orchestrator...")
    orchestrator = EPMAuditOrchestrator(args.config)
    
    # Run audit based on arguments
    if args.app:
        # Single app
        print(f"\nAuditing: {args.app}")
        results = [orchestrator.audit_app(args.app, args.days)]
    elif args.env:
        # All apps in environment
        print(f"\nAuditing {args.env} environment...")
        results = orchestrator.audit_environment(args.env, args.days)
    elif args.sox_only:
        # SOX-critical apps
        print("\nAuditing SOX-critical applications...")
        results = orchestrator.audit_sox_critical(args.days)
    else:
        print("Error: Specify --app, --env, or --sox-only")
        return
    
    # Save results
    print("\n" + "="*60)
    print("Saving results...")
    orchestrator.save_results(results, Path(args.output))
    
    # Print summary
    print("\n" + "="*60)
    print("AUDIT SUMMARY")
    print("="*60)
    
    for result in results:
        if 'error' in result:
            print(f"\n✗ {result['app_id']}: FAILED")
            print(f"   Error: {result['error']}")
        else:
            print(f"\n✓ {result['app_name']} ({result['environment']})")
            print(f"   Changes: {result['summary']['total_changes']}")
            print(f"   Material: {result['summary']['material_changes']}")
            print(f"   SOX Critical: {result['summary']['sox_critical']}")
            
            if result['summary']['sox_critical'] > 0:
                print(f"   ⚠️  ACTION REQUIRED")
    
    print("\n" + "="*60)
    print("Audit complete. Results saved to:", args.output)


if __name__ == '__main__':
    main()
