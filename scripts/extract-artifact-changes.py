#!/usr/bin/env python3
"""
EPM Artifact Audit Extractor

Generates Artifact Updates Report via Oracle REST API and classifies
changes as operational noise vs. material configuration changes.

Usage:
    python extract-artifact-changes.py --config config.yaml
    python extract-artifact-changes.py --url https://... --user ...

Output:
    - Raw CSV report (from Oracle)
    - Filtered JSON (material changes only)
    - SOX summary report
"""

import argparse
import csv
import json
import logging
import requests
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class EPMArtifactExtractor:
    """Extract and classify EPM artifact changes"""
    
    # Operational artifact types (noise)
    OPERATIONAL_TYPES = {
        'PERIOD', 'PERIOD_STATUS', 'JOB', 'CONSOLIDATION_EXECUTION',
        'JOURNAL_POSTING', 'FORM_SAVE', 'DATA_ENTRY', 'CALCULATION_RUN',
        'APPROVAL_PROMOTION', 'REQUEST_APPROVAL', 'SNAPSHOT_RESTORE',
        'BACKUP', 'REPLICATION'
    }
    
    # Configuration artifact types (material)
    CONFIGURATION_TYPES = {
        'CONSOLIDATION_RULE', 'BUSINESS_RULE', 'CALCULATION_RULE',
        'DATA_FORM', 'COMPOSITE_FORM', 'DIMENSION', 'ATTRIBUTE',
        'SMART_LIST', 'SUBSTITUTION_VARIABLE', 'CURRENCY_TABLE',
        'ALLOCATION_RULE', 'RECONCILIATION_FORMAT', 'MATCHING_RULE',
        'VALIDATION_RULE', 'DATA_LOAD_RULE', 'IMPORT_FORMAT'
    }
    
    def __init__(self, instance_url: str, username: str, password: str):
        self.base_url = instance_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def generate_report(self, from_date: str, to_date: str, 
                        output_filename: str = None) -> str:
        """
        Generate Artifact Updates Report via REST API
        
        Returns: Generated filename (saved to Outbox)
        """
        if not output_filename:
            output_filename = f"Artifact_Updates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        endpoint = f"{self.base_url}/interop/rest/v1/applicationsnapshots/reports/artifactupdates"
        
        # Ensure dates are ISO 8601 format
        if 'T' not in from_date:
            from_date = f"{from_date}T00:00:00"
        if 'T' not in to_date:
            to_date = f"{to_date}T23:59:59"
        
        payload = {
            "fileName": output_filename,
            "modifiedBy": "All",
            "artifactType": "All",
            "fromDate": from_date,
            "toDate": to_date
        }
        
        self.logger.info(f"Generating report: {output_filename}")
        self.logger.info(f"Period: {from_date} to {to_date}")
        
        try:
            response = self.session.post(endpoint, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('status') == 'SUCCESS':
                self.logger.info(f"✓ Report generated: {output_filename}")
                self.logger.info(f"✓ Saved to Outbox")
                return output_filename
            else:
                self.logger.error(f"✗ Report generation failed: {result}")
                return None
                
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP Error: {e}")
            if e.response.text:
                self.logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            self.logger.error(f"Error: {e}")
            return None
    
    def download_report(self, filename: str, output_path: Path) -> bool:
        """
        Download report from Outbox
        """
        # For EPM Automate, we'd use: epmautomate downloadFile
        # For REST API, we need a different approach
        
        # Note: Download via REST requires Files API
        # This is a placeholder - actual implementation varies
        
        self.logger.info(f"Downloading {filename} to {output_path}")
        
        # Alternative: Use EPM Automate CLI
        import subprocess
        try:
            result = subprocess.run(
                ['epmautomate', 'downloadFile', filename, str(output_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.logger.info(f"✓ Downloaded: {output_path}")
                return True
            else:
                self.logger.error(f"✗ Download failed: {result.stderr}")
                return False
                
        except FileNotFoundError:
            self.logger.error("epmautomate CLI not found")
            return False
        except Exception as e:
            self.logger.error(f"Error: {e}")
            return False
    
    def classify_change(self, artifact: Dict) -> Dict:
        """
        Classify artifact change as operational or material
        """
        artifact_type = (artifact.get('Artifact Type', '') or 
                        artifact.get('artifactType', '')).upper()
        artifact_name = (artifact.get('Artifact Name', '') or 
                        artifact.get('artifactName', '')).lower()
        
        # Determine category
        if any(t in artifact_type for t in self.OPERATIONAL_TYPES):
            category = 'OPERATIONAL'
            material = False
        elif any(t in artifact_type for t in self.CONFIGURATION_TYPES):
            category = 'CONFIGURATION'
            material = True
        else:
            category = 'UNKNOWN'
            material = None  # Requires review
        
        # SOX materiality check
        sox_critical = False
        if material:
            # Critical artifacts for SOX
            critical_patterns = [
                'CONSOLIDATION_RULE', 'ELIMINATION', 'CURRENCY_TRANSLATION',
                'ACCOUNT', 'ENTITY', 'CALCULATION', 'ALLOCATION'
            ]
            sox_critical = any(p in artifact_type for p in critical_patterns)
        
        # Analysis notes
        analysis = {
            'category': category,
            'material': material,
            'sox_critical': sox_critical,
            'requires_approval': material,
            'alert_severity': 'HIGH' if sox_critical else ('MEDIUM' if material else 'INFO')
        }
        
        return {**artifact, **analysis}
    
    def process_csv(self, csv_path: Path) -> Dict:
        """
        Process Artifact Updates Report CSV
        
        Returns dict with:
        - all_changes: List of all artifacts
        - material_changes: List of material changes
        - summary: Statistics
        """
        self.logger.info(f"Processing CSV: {csv_path}")
        
        all_changes = []
        material_changes = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Classify change
                    classified = self.classify_change(row)
                    all_changes.append(classified)
                    
                    if classified['material']:
                        material_changes.append(classified)
            
            # Generate summary
            summary = {
                'total_artifacts': len(all_changes),
                'material_changes': len(material_changes),
                'operational_changes': len([c for c in all_changes if c['category'] == 'OPERATIONAL']),
                'unknown_changes': len([c for c in all_changes if c['category'] == 'UNKNOWN']),
                'sox_critical': len([c for c in all_changes if c['sox_critical']])
            }
            
            self.logger.info(f"✓ Processed {summary['total_artifacts']} artifacts")
            self.logger.info(f"  - Material: {summary['material_changes']}")
            self.logger.info(f"  - Operational: {summary['operational_changes']}")
            self.logger.info(f"  - SOX Critical: {summary['sox_critical']}")
            
            return {
                'all_changes': all_changes,
                'material_changes': material_changes,
                'summary': summary
            }
            
        except Exception as e:
            self.logger.error(f"Error processing CSV: {e}")
            return None
    
    def save_results(self, data: Dict, output_dir: Path):
        """
        Save processed results
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save all changes (JSON)
        all_json = output_dir / f'artifact_changes_{timestamp}.json'
        with open(all_json, 'w') as f:
            json.dump(data['all_changes'], f, indent=2, default=str)
        self.logger.info(f"✓ Saved: {all_json}")
        
        # Save material changes only
        if data['material_changes']:
            material_json = output_dir / f'material_changes_{timestamp}.json'
            with open(material_json, 'w') as f:
                json.dump(data['material_changes'], f, indent=2, default=str)
            self.logger.info(f"✓ Saved: {material_json}")
        
        # Save summary
        summary_json = output_dir / f'summary_{timestamp}.json'
        with open(summary_json, 'w') as f:
            json.dump(data['summary'], f, indent=2)
        self.logger.info(f"✓ Saved: {summary_json}")
        
        # Generate CSV report (material only)
        if data['material_changes']:
            csv_path = output_dir / f'material_changes_{timestamp}.csv'
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=data['material_changes'][0].keys())
                writer.writeheader()
                writer.writerows(data['material_changes'])
            self.logger.info(f"✓ Saved: {csv_path}")


def main():
    parser = argparse.ArgumentParser(
        description='EPM Artifact Audit Extractor'
    )
    parser.add_argument('--url', required=True, 
                       help='EPM instance URL')
    parser.add_argument('--user', required=True,
                       help='Username (username@domain)')
    parser.add_argument('--password', required=True,
                       help='Password')
    parser.add_argument('--days', type=int, default=1,
                       help='Number of days to look back (default: 1)')
    parser.add_argument('--from-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--to-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--csv', help='Process existing CSV file instead of generating')
    parser.add_argument('--output', default='./outputs/artifacts',
                       help='Output directory')
    
    args = parser.parse_args()
    
    extractor = EPMArtifactExtractor(
        args.url, args.user, args.password
    )
    
    # Determine date range
    if args.from_date and args.to_date:
        from_date = args.from_date
        to_date = args.to_date
    else:
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
    
    print(f"\n{'='*60}")
    print(f"EPM Artifact Audit Extractor")
    print(f"{'='*60}\n")
    
    # Process existing CSV or generate new report
    if args.csv:
        csv_path = Path(args.csv)
        if not csv_path.exists():
            print(f"Error: CSV file not found: {csv_path}")
            sys.exit(1)
    else:
        # Generate report via API
        print(f"Generating report for {from_date} to {to_date}...")
        
        report_name = extractor.generate_report(from_date, to_date)
        if not report_name:
            print("\n✗ Report generation failed")
            sys.exit(1)
        
        # Download (requires EPM Automate CLI)
        print("\nNote: Download step requires 'epmautomate' CLI")
        print(f"Run manually: epmautomate downloadFile {report_name}")
        print(f"Then re-run with: --csv /path/to/{report_name}")
        
        # Skip processing if we can't download
        print("\nReport generated in cloud Outbox.")
        print("Download manually and re-run with --csv option.")
        sys.exit(0)
    
    # Process CSV
    print(f"\nProcessing CSV: {csv_path}")
    results = extractor.process_csv(csv_path)
    
    if not results:
        print("\n✗ Processing failed")
        sys.exit(1)
    
    # Save results
    print(f"\nSaving results to {args.output}...")
    extractor.save_results(results, Path(args.output))
    
    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total Artifacts:     {results['summary']['total_artifacts']}")
    print(f"Material Changes:    {results['summary']['material_changes']}")
    print(f"Operational:         {results['summary']['operational_changes']}")
    print(f"SOX Critical:        {results['summary']['sox_critical']}")
    print(f"{'='*60}\n")
    
    # Alert if SOX critical found
    if results['summary']['sox_critical'] > 0:
        print("⚠️  ALERT: SOX-critical changes detected!")
        critical = [c for c in results['material_changes'] if c['sox_critical']]
        for c in critical[:5]:
            print(f"  - {c.get('Artifact Name', 'Unknown')}")
    
    print("✓ Extraction complete")


if __name__ == '__main__':
    main()
