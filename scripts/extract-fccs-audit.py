#!/usr/bin/env python3
"""
FCCS Audit Data Extraction Script

Extracts journal entries, period status, and consolidation metadata
for SOX compliance and internal control monitoring.

Usage:
    python extract-fccs-audit.py --env prod --date 2026-02-26
    python extract-fccs-audit.py --env prod --period Feb-26
    python extract-fccs-audit.py --env prod --range 2026-02-01 2026-02-26
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
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError:
    print("Error: requests library required. Run: pip install requests")
    sys.exit(1)


class FCCSExtractor:
    """Extracts audit data from FCCS via REST API"""
    
    def __init__(self, config: Dict):
        self.base_url = config['url']
        self.username = config['username']
        self.password = config['password']
        self.application = config['application']
        self.api_version = config.get('api_version', 'v1')
        
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.username, self.password)
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to FCCS API"""
        url = f"{self.base_url}/epm/rest/{self.api_version}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.logger.error("Authentication failed - check credentials")
            elif e.response.status_code == 404:
                self.logger.error(f"Endpoint not found: {endpoint}")
            else:
                self.logger.error(f"HTTP error: {e}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return None
    
    def get_journal_entries(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Extract journal entries for date range
        
        SOX Relevance: Tracks all manual and automated journal entries
        with approval workflow and posting details.
        """
        self.logger.info(f"Fetching journal entries from {start_date} to {end_date}")
        
        endpoint = f"applications/{self.application}/journals"
        params = {
            'startDate': start_date,
            'endDate': end_date,
            'limit': 1000  # Pagination if needed
        }
        
        data = self._make_request(endpoint, params)
        
        if not data or 'items' not in data:
            self.logger.warning("No journal entries found")
            return []
        
        journals = []
        for item in data['items']:
            journal = {
                'journal_id': item.get('journalId'),
                'journal_name': item.get('journalName'),
                'description': item.get('description'),
                'created_by': item.get('createdBy'),
                'created_date': item.get('createdDate'),
                'posted_by': item.get('postedBy'),
                'posted_date': item.get('postedDate'),
                'status': item.get('status'),  # WORKING, POSTED, etc.
                'total_debits': item.get('totalDebits'),
                'total_credits': item.get('totalCredits'),
                'period': item.get('periodName'),
                'year': item.get('yearName'),
                'adjustment_type': item.get('adjustmentType'),  # True = adjustment
                'extraction_timestamp': datetime.now().isoformat()
            }
            journals.append(journal)
        
        self.logger.info(f"Extracted {len(journals)} journal entries")
        return journals
    
    def get_period_status(self, year: str, period: str) -> Optional[Dict]:
        """
        Get period close status
        
        SOX Relevance: Evidence of period close timeline and approvals
        """
        self.logger.info(f"Fetching period status for {year}-{period}")
        
        endpoint = f"applications/{self.application}/calendars/{year}/periods/{period}"
        data = self._make_request(endpoint)
        
        if not data:
            return None
        
        return {
            'year': year,
            'period': period,
            'status': data.get('status'),  # OPEN, CLOSED, LOCKED
            'start_date': data.get('startDate'),
            'end_date': data.get('endDate'),
            'closed_by': data.get('closedBy'),
            'closed_date': data.get('closedDate'),
            'extraction_timestamp': datetime.now().isoformat()
        }
    
    def get_consolidation_status(self, year: str, period: str) -> Optional[Dict]:
        """
        Get consolidation execution status
        
        SOX Relevance: Proof of consolidation execution and success
        """
        self.logger.info(f"Fetching consolidation status for {year}-{period}")
        
        # Consolidation metadata via job status
        endpoint = f"applications/{self.application}/jobs"
        params = {
            'jobType': 'CONSOLIDATE',
            'period': period,
            'year': year,
            'limit': 100
        }
        
        data = self._make_request(endpoint, params)
        
        if not data or 'items' not in data:
            return None
        
        consolidations = []
        for item in data['items']:
            cons = {
                'job_id': item.get('jobId'),
                'job_name': item.get('jobName'),
                'status': item.get('status'),  # SUCCESS, FAILED, RUNNING
                'started_by': item.get('startedBy'),
                'start_time': item.get('startTime'),
                'end_time': item.get('endTime'),
                'duration_seconds': item.get('duration'),
                'rules_executed': item.get('rulesExecuted', []),
                'extraction_timestamp': datetime.now().isoformat()
            }
            consolidations.append(cons)
        
        return {
            'year': year,
            'period': period,
            'consolidation_count': len(consolidations),
            'consolidations': consolidations
        }
    
    def get_security_audit(self) -> Dict:
        """
        Extract user and group security configuration
        
        SOX Relevance: Access control evidence
        """
        self.logger.info("Fetching security configuration")
        
        # Users
        users_endpoint = f"applications/{self.application}/security/users"
        users_data = self._make_request(users_endpoint)
        
        users = []
        if users_data and 'items' in users_data:
            for user in users_data['items']:
                users.append({
                    'user_id': user.get('userId'),
                    'user_name': user.get('userName'),
                    'email': user.get('email'),
                    'active': user.get('active'),
                    'groups': user.get('groups', []),
                    'last_login': user.get('lastLogin'),
                    'extraction_timestamp': datetime.now().isoformat()
                })
        
        # Groups
        groups_endpoint = f"applications/{self.application}/security/groups"
        groups_data = self._make_request(groups_endpoint)
        
        groups = []
        if groups_data and 'items' in groups_data:
            for group in groups_data['items']:
                groups.append({
                    'group_id': group.get('groupId'),
                    'group_name': group.get('groupName'),
                    'member_count': len(group.get('members', [])),
                    'extraction_timestamp': datetime.now().isoformat()
                })
        
        return {
            'user_count': len(users),
            'group_count': len(groups),
            'users': users,
            'groups': groups
        }


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


def load_config(env_name: str) -> Dict:
    """Load environment configuration"""
    config_path = Path(__file__).parent.parent / 'config' / 'environments.yaml'
    
    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
            return config['fccs'][env_name]
    except FileNotFoundError:
        # Fallback to placeholder for demo
        print(f"Warning: Config file not found at {config_path}")
        print("Using placeholder configuration - update for production use")
        return {
            'url': 'https://YOUR-FCCS-INSTANCE.epm.us-phoenix-1.ocs.oraclecloud.com',
            'username': 'YOUR_USERNAME',
            'password': 'YOUR_PASSWORD',
            'application': 'YOUR_APPLICATION_NAME'
        }
    except ImportError:
        print("Warning: PyYAML not installed. Install with: pip install pyyaml")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='FCCS Audit Data Extraction')
    parser.add_argument('--env', required=True, help='Environment name (prod, test, dev)')
    parser.add_argument('--date', help='Single date (YYYY-MM-DD)')
    parser.add_argument('--period', help='Period name (e.g., Feb-26)')
    parser.add_argument('--year', default=str(datetime.now().year), help='Fiscal year')
    parser.add_argument('--range', nargs=2, metavar=('START', 'END'), help='Date range')
    parser.add_argument('--output', default='./outputs/fccs', help='Output directory')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both',
                       help='Output format')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.env)
    
    # Initialize extractor
    extractor = FCCSExtractor(config)
    
    # Create output directory with date stamp
    output_dir = Path(args.output) / datetime.now().strftime('%Y-%m-%d')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"FCCS Audit Extraction - {args.env.upper()}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}\n")
    
    # Determine date range
    if args.range:
        start_date, end_date = args.range
    elif args.date:
        start_date = end_date = args.date
    else:
        # Default to yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = end_date = yesterday
    
    period = args.period or datetime.now().strftime('%b-%y')
    
    # Extract data
    print("\n--- Extracting Journal Entries ---")
    journals = extractor.get_journal_entries(start_date, end_date)
    if args.format in ['json', 'both']:
        save_json({'journals': journals}, output_dir / f'journals_{start_date}_{end_date}.json')
    if args.format in ['csv', 'both'] and journals:
        save_csv(journals, output_dir / f'journals_{start_date}_{end_date}.csv')
    
    print("\n--- Extracting Period Status ---")
    period_status = extractor.get_period_status(args.year, period)
    if period_status:
        save_json({'period_status': period_status}, output_dir / f'period_status_{args.year}_{period}.json')
    
    print("\n--- Extracting Consolidation Status ---")
    consol_status = extractor.get_consolidation_status(args.year, period)
    if consol_status:
        save_json({'consolidation': consol_status}, output_dir / f'consolidation_{args.year}_{period}.json')
    
    print("\n--- Extracting Security Audit ---")
    security = extractor.get_security_audit()
    save_json({'security': security}, output_dir / f'security_{datetime.now().strftime("%Y%m%d")}.json')
    
    print(f"\n{'='*60}")
    print("Extraction Complete")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
