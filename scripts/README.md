# EPM Audit Extraction Scripts

## Available Scripts

### Core Extraction Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `extract-fccs-audit.py` | FCCS journals, period status, consolidation | `python extract-fccs-audit.py --env prod --date 2026-02-26` |
| `extract-oci-audit.py` | OCI IAM changes, audit logs | `python extract-oci-audit.py --compartment ocid1... --days 7` |

### Coming Soon

- `extract-pbcs-audit.py` - PBCS planning data, approvals
- `extract-edm-audit.py` - EDM hierarchy changes, requests
- `extract-arcs-audit.py` - ARCS reconciliations, transactions
- `extract-trcs-audit.py` - TRCS tax provision data
- `extract-pcm-audit.py` - PCM allocations, trace data
- `consolidate-reports.py` - Cross-application SOX reporting

## Prerequisites

### All Scripts
```bash
pip install pyyaml requests
```

### OCI Scripts
```bash
pip install oci
oci setup config  # Run interactive setup
```

### EPM REST API Scripts
- Valid EPM Cloud service account
- Appropriate application permissions (typically Service Administrator or Audit Viewer)

## Configuration

1. **Copy the template:**
   ```bash
   cp config/environments.yaml config/environments.yaml.local
   ```

2. **Fill in your environment details:**
   - OCI compartment OCIDs
   - EPM instance URLs
   - Service account credentials (use OCI Vault in production)

3. **Secure your credentials:**
   ```bash
   chmod 600 config/environments.yaml.local
   git add config/environments.yaml.local  # Already in .gitignore
   ```

## Running Extractions

### FCCS Example
```bash
# Yesterday's data
python extract-fccs-audit.py --env prod

# Specific date range
python extract-fccs-audit.py --env prod --range 2026-02-01 2026-02-26

# Specific period
python extract-fccs-audit.py --env prod --period Feb-26 --year FY26
```

### OCI Example
```bash
# Last 24 hours, SOX-critical events only
python extract-oci-audit.py --compartment ocid1.compartment.oc1..xxx --sox-only

# Access summary snapshot
python extract-oci-audit.py --compartment ocid1.compartment.oc1..xxx --include-access-summary

# Date range with full audit trail
python extract-oci-audit.py --compartment ocid1.compartment.oc1..xxx \
    --start 2026-02-01 --end 2026-02-26
```

## Output Format

All scripts produce:
- **JSON:** Complete structured data for API/integration
- **CSV:** Human-readable for Excel/analysis

Output directory structure:
```
outputs/
├── fccs/
│   └── 2026-02-26/
│       ├── journals_2026-02-26_2026-02-26.json
│       ├── journals_2026-02-26_2026-02-26.csv
│       ├── period_status_FY26_Feb-26.json
│       ├── consolidation_FY26_Feb-26.json
│       └── security_20260226.json
└── oci/
    └── 2026-02-26/
        ├── audit_events_20260201_20260226.json
        ├── audit_events_20260201_20260226.csv
        └── access_summary_20260226.json
```

## Scheduling (Cron)

Example crontab entries:

```bash
# Daily at 2 AM - FCCS
0 2 * * * cd /path/to/epm-audit-automation && python scripts/extract-fccs-audit.py --env prod >> logs/fccs-cron.log 2>&1

# Daily at 3 AM - OCI
0 3 * * * cd /path/to/epm-audit-automation && python scripts/extract-oci-audit.py --compartment ocid1... --sox-only >> logs/oci-cron.log 2>&1

# Weekly on Sunday - Full access review
0 4 * * 0 cd /path/to/epm-audit-automation && python scripts/extract-oci-audit.py --compartment ocid1... --include-access-summary >> logs/oci-weekly.log 2>&1
```

## Security Best Practices

1. **Never commit credentials** - Use OCI Vault or environment variables
2. **Encrypt at rest** - Enable encryption in `environments.yaml`
3. **Rotate service accounts** - Set up 90-day rotation alerts
4. **Least privilege** - Service accounts should have minimum required permissions
5. **Audit the auditors** - Log all extraction activities

## Troubleshooting

### Authentication Errors
```
HTTP 401: Check credentials in config file
HTTP 403: Service account lacks required permissions
HTTP 404: Wrong application name or endpoint URL
```

### OCI Errors
```
ServiceError: Check OCI config file and API key permissions
NotAuthorizedOrNotFound: Verify compartment OCID and user permissions
```

### Data Not Found
- Check date format (YYYY-MM-DD)
- Verify period naming convention (e.g., "Feb-26" vs "February 2026")
- Ensure service account has access to the specific application

## Customization

To add a new extraction point:

1. Add endpoint to `docs/audit-extraction-matrix.md`
2. Implement extraction method in appropriate script
3. Update SOX mapping in `docs/sox-control-mapping.md`
4. Add test cases

---

*See project README.md for full documentation*
