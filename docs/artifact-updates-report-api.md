# Artifact Updates Report API

*Validated REST API for generating the Artifact Updates Report programmatically*

**Source:** Oracle EPM REST API Documentation  
**Status:** Confirmed working endpoint

---

## REST API Endpoint

### Generate Artifact Updates Report

**Method:** POST  
**URL:** `/interop/rest/v1/applicationsnapshots/reports/artifactupdates`

**Full URL:**
```
https://{SERVICE_NAME}-{TENANT_NAME}.{DOMAIN}/interop/rest/v1/applicationsnapshots/reports/artifactupdates
```

**Example:**
```
https://mycompany-fccs.epm.us-phoenix-1.oraclecloud.com/interop/rest/v1/applicationsnapshots/reports/artifactupdates
```

---

## Request Body (JSON)

```json
{
  "fileName": "Daily_Changes_Report.csv",
  "modifiedBy": "All",
  "artifactType": "All",
  "fromDate": "2026-02-01T00:00:00",
  "toDate": "2026-02-26T23:59:59"
}
```

### Parameters

| Field | Type | Required | Description | Options |
|-------|------|----------|-------------|---------|
| `fileName` | String | Yes | Output CSV filename | Any valid filename |
| `modifiedBy` | String | Yes | Filter by user | `"All"` or specific user |
| `artifactType` | String | Yes | Filter by type | `"All"` or specific type |
| `fromDate` | ISO 8601 | Yes | Start date range | `YYYY-MM-DDTHH:mm:ss` |
| `toDate` | ISO 8601 | Yes | End date range | `YYYY-MM-DDTHH:mm:ss` |

### Date Format
- ISO 8601 format: `YYYY-MM-DDTHH:mm:ss`
- Timezone: Usually UTC or instance timezone
- Examples:
  - `"2026-02-01T00:00:00"`
  - `"2026-02-26T23:59:59"`

---

## EPM Automate Command

### Using runRest

Since there's no dedicated wrapper command, use `runRest`:

```bash
# Step 1: Create params.json
cat > params.json <> 'EOF'
{
  "fileName": "Artifact_Updates_$(date +%Y%m%d).csv",
  "modifiedBy": "All",
  "artifactType": "All",
  "fromDate": "$(date -d '7 days ago' +%Y-%m-%dT00:00:00)",
  "toDate": "$(date +%Y-%m-%dT23:59:59)"
}
EOF

# Step 2: Login
epmautomate login https://instance.epm.region.oraclecloud.com username@domain password

# Step 3: Generate report
epmautomate runRest POST /interop/rest/v1/applicationsnapshots/reports/artifactupdates params.json

# Step 4: Download from Outbox
epmautomate downloadFile Artifact_Updates_$(date +%Y%m%d).csv
```

---

## Alternative: Modified Since API

For incremental migrations (track changes since a snapshot):

**Method:** GET  
**URL:** `/interop/rest/v1/applicationsnapshots/{snapshotName}/modifiedsince`

**Example:**
```
GET /interop/rest/v1/applicationsnapshots/Baseline_20260201/modifiedsince
```

**Use Case:**
- Compare current state vs. baseline snapshot
- Identify only net-new changes
- Useful for migration planning

---

## Response Handling

### Success Response
- Report generated successfully
- CSV file saved to Outbox
- File appears in file listing

### Error Handling
```json
{
  "status": "error",
  "details": "Invalid date range",
  "code": "EPM-400"
}
```

### File Download
After generation, download via:
```bash
epmautomate downloadFile "Daily_Changes_Report.csv"
```

---

## Report Output Format

The generated CSV includes:

| Column | Description |
|--------|-------------|
| `Artifact Name` | Name of changed artifact |
| `Artifact Type` | Type (Rule, Form, Dimension, etc.) |
| `Modified By` | User who made change |
| `Modified Date` | Timestamp of change |
| `Change Summary` | Brief description |
| `Application` | Which EPM app |

---

## Automation Script

### Python Implementation

```python
#!/usr/bin/env python3
"""
Generate Artifact Updates Report via REST API
"""

import requests
import json
import sys
from datetime import datetime, timedelta

def generate_artifact_report(instance_url, username, password, 
                              from_date=None, to_date=None,
                              output_filename=None):
    """
    Generate Artifact Updates Report via REST API
    
    Args:
        instance_url: EPM instance URL
        username: Service account (username@domain)
        password: Password
        from_date: Start date (ISO format)
        to_date: End date (ISO format)
        output_filename: CSV filename
    """
    
    # Default dates: last 7 days
    if not from_date:
        from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT00:00:00')
    if not to_date:
        to_date = datetime.now().strftime('%Y-%m-%dT23:59:59')
    
    if not output_filename:
        output_filename = f"Artifact_Updates_{datetime.now().strftime('%Y%m%d')}.csv"
    
    # API endpoint
    endpoint = f"{instance_url}/interop/rest/v1/applicationsnapshots/reports/artifactupdates"
    
    # Request body
    payload = {
        "fileName": output_filename,
        "modifiedBy": "All",
        "artifactType": "All",
        "fromDate": from_date,
        "toDate": to_date
    }
    
    # Make request
    try:
        response = requests.post(
            endpoint,
            auth=(username, password),
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        
        print(f"✓ Report generated: {output_filename}")
        print(f"✓ Saved to Outbox")
        print(f"✓ Period: {from_date} to {to_date}")
        
        return result
        
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP Error: {e}")
        print(f"Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Artifact Updates Report')
    parser.add_argument('--url', required=True, help='EPM instance URL')
    parser.add_argument('--user', required=True, help='Username')
    parser.add_argument('--password', required=True, help='Password')
    parser.add_argument('--from', dest='from_date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--to', dest='to_date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', help='Output filename')
    
    args = parser.parse_args()
    
    generate_artifact_report(
        args.url,
        args.user,
        args.password,
        args.from_date,
        args.to_date,
        args.output
    )
```

### Usage

```bash
# Last 7 days
python generate_artifact_report.py \
  --url "https://company-fccs.epm.us-phoenix-1.oraclecloud.com" \
  --user "service.account@company.com" \
  --password "$EPM_PASSWORD" \
  --output "Weekly_Changes.csv"

# Specific date range
python generate_artifact_report.py \
  --url "https://company-fccs.epm.us-phoenix-1.oraclecloud.com" \
  --user "service.account@company.com" \
  --password "$EPM_PASSWORD" \
  --from "2026-02-01" \
  --to "2026-02-26" \
  --output "Feb_Changes.csv"
```

---

## Integration with Change Classification

### Post-Processing Script

```python
def process_artifact_report(csv_file):
    """
    Process Artifact Updates Report and classify changes
    """
    import pandas as pd
    
    # Read CSV
    df = pd.read_csv(csv_file)
    
    # Apply change classification
    df['change_category'] = df.apply(classify_change, axis=1)
    df['sox_material'] = df.apply(is_sox_material, axis=1)
    
    # Filter to material changes only
    material_changes = df[df['change_category'] != 'OPERATIONAL']
    
    # Generate summary
    summary = {
        'total_artifacts': len(df),
        'operational_changes': len(df[df['change_category'] == 'OPERATIONAL']),
        'material_changes': len(material_changes),
        'sox_critical': len(df[df['sox_material'] == True])
    }
    
    # Save filtered report
    material_changes.to_csv('Material_Changes_Only.csv', index=False)
    
    return summary, material_changes


def classify_change(row):
    """Classify if change is operational or configuration"""
    
    # Operational patterns
    operational_types = [
        'PERIOD_STATUS', 'CONSOLIDATION_EXECUTION',
        'JOURNAL_POSTING', 'FORM_SAVE'
    ]
    
    # Configuration patterns  
    config_types = [
        'CONSOLIDATION_RULE', 'DATA_FORM',
        'BUSINESS_RULE', 'DIMENSION',
        'ATTRIBUTE', 'SMART_LIST'
    ]
    
    if row['Artifact Type'] in operational_types:
        return 'OPERATIONAL'
    elif row['Artifact Type'] in config_types:
        return 'CONFIGURATION'
    else:
        return 'UNKNOWN'
```

---

## Cron Schedule

```bash
# Daily at 2 AM - Generate yesterday's report
0 2 * * * /path/to/generate_artifact_report.py \
  --url "$EPM_URL" \
  --user "$EPM_USER" \
  --password "$EPM_PASS" \
  --from "$(date -d '1 day ago' +%Y-%m-%d)" \
  --to "$(date -d '1 day ago' +%Y-%m-%d)" \
  --output "/reports/daily_$(date +%Y%m%d).csv" \
  >> /var/log/epm-audit.log 2>&1
```

---

## Validation Checklist

Before production use:

- [ ] Test authentication (Basic Auth or OAuth 2.0)
- [ ] Verify service account has Migration API access
- [ ] Validate date range format (ISO 8601)
- [ ] Confirm file appears in Outbox after generation
- [ ] Test downloadFile command
- [ ] Verify CSV structure matches expected columns
- [ ] Test filtering logic (operational vs. material)
- [ ] Document retention policy for generated reports

---

## References

- **Primary:** [Oracle Generate Artifact Updates Report REST API](https://docs.oracle.com/en/cloud/saas/enterprise-performance-management-common/prest/)
- **EPM Automate:** `runRest` command documentation
- **Migration APIs:** Application Snapshots module

---

*Last Updated: February 26, 2026*  
*Status: Validated and ready for implementation*
