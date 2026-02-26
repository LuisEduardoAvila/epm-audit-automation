# SOX Control Mapping for EPM Automation

*Maps EPM audit extraction points to specific SOX control objectives*

---

## SOX 302 - Corporate Responsibility for Financial Reports

### CEO/CFO Certification Support

| Control ID | Control Description | EPM Evidence Required | Extraction Source |
|------------|-------------------|----------------------|-------------------|
| **302.1** | All material info disclosed | Period close completion evidence | FCCS Period Status + Task Manager |
| **302.2** | No material misstatements | Reconciliation certification status | ARCS Reconciliation Report |
| **302.3** | Internal controls effective | Control execution logs | All apps + OCI Audit |

#### Key 302 Artifacts
```yaml
Daily Extraction:
  - FCCS:
      - Period_Close_Status: "All periods closed as of [timestamp]"
      - Consolidation_Rules_Executed: [list of rules with timestamps]
      - Journal_Entry_Count: "N manual entries, M automated entries"
  
  - ARCS:
      - Uncertified_Reconciliations: [list of late items]
      - Aging_Buckets: "30d: X, 60d: Y, 90d+: Z"
      - Material_Threshold_Breaches: [items > $threshold uncertified]
```

---

## SOX 404 - Management Assessment of Internal Controls

### Control Environment (COSO Framework)

| COSO Component | EPM Control | Extraction Point | Frequency |
|----------------|-------------|------------------|-----------|
| **Control Activities** | User access provisioning | IAM changes (OCI) + EPM security | Weekly |
| **Control Activities** | Segregation of duties | Security filter assignments | Weekly |
| **Monitoring** | Automated control execution | Rule execution logs | Daily |
| **Information & Communication** | Data integrity checks | Data Exchange error logs | Daily |
| **Risk Assessment** | Master data changes | EDM hierarchy audit | Daily |

---

## Automated Control Matrix

### 1. Access Controls (AC)

| AC ID | Control Name | Automated Test | Data Source | Pass Criteria |
|-------|--------------|----------------|-------------|---------------|
| **AC-01** | User Provisioning | Detect new users without approved access request | OCI IAM Create Events + ServiceNow | No orphan users > 24h |
| **AC-02** | User Deprovisioning | Detect terminated users with active access | HR feed vs OCI/EPM users | No terminated users with access |
| **AC-03** | Privileged Access | Track admin role assignments | EPM Admin groups + OCI policies | Admin access reviewed monthly |
| **AC-04** | Segregation of Duties | Check SOD matrix violations | EPM security assignments | Zero SOD violations |

**Extraction Queries:**
```sql
-- AC-01: New users without approval
SELECT user_id, creation_date, approver 
FROM oci_audit_logs 
WHERE event_name = 'CreateUser' 
  AND creation_date > SYSDATE - 1
  AND user_id NOT IN (SELECT user_id FROM approved_access_requests);

-- AC-02: Terminated users with access
SELECT hr.user_id, hr.termination_date, oci.active 
FROM hr_termination_feed hr
JOIN oci_users oci ON hr.user_id = oci.user_id
WHERE oci.active = 'TRUE' 
  AND hr.termination_date < SYSDATE;
```

---

### 2. Change Management Controls (CM)

| CM ID | Control Name | Automated Test | Data Source | Pass Criteria |
|-------|--------------|----------------|-------------|---------------|
| **CM-01** | EDM Changes Approved | All hierarchy changes have approved request | EDM Request History | 100% approval coverage |
| **CM-02** | FCCS Rules Tested | Rule changes tested before production | FCCS rule deployment log | Test evidence linked |
| **CM-03** | Emergency Changes | Emergency changes documented and approved | Change log with emergency flag | Emergency < 5% of changes |
| **CM-04** | Period Lock | No changes after period close | FCCS period status + change log | Zero post-close modifications |

**Extraction Queries:**
```python
# CM-01: Unapproved EDM changes
edm_requests = extract_edm_requests(since=yesterday)
unapproved = [r for r in edm_requests if r.approval_status != 'APPROVED']
alert_if(unapproved, "Unapproved EDM changes detected")

# CM-04: Post-close modifications
period_status = get_fccs_period_status()
if period_status.state == 'CLOSED':
    changes = get_fccs_changes(since=period_status.close_date)
    if changes:
        raise_sox_exception("Changes detected after period close")
```

---

### 3. Data Integrity Controls (DI)

| DI ID | Control Name | Automated Test | Data Source | Pass Criteria |
|-------|--------------|----------------|-------------|---------------|
| **DI-01** | Data Load Balanced | Source to target record count matches | Data Exchange logs | Variance < 0.1% |
| **DI-02** | Error Resolution | All load errors resolved within SLA | Data Exchange error log | Zero errors > 48h old |
| **DI-03** | Manual JE Review | All manual journals have approval | FCCS journal entries | 100% approval before posting |
| **DI-04** | Intercompany Balanced | I/C differences identified and explained | FCCS I/C matching | Zero unmatched > threshold |
| **DI-05** | Reconciliation Complete | All material accounts certified | ARCS status | 100% certified before close |

**Extraction Queries:**
```python
# DI-01: Source-to-target validation
def validate_data_load(load_id):
    source_count = get_source_record_count(load_id)
    target_count = get_target_record_count(load_id)
    variance_pct = abs(source_count - target_count) / source_count
    
    if variance_pct > 0.001:  # 0.1% threshold
        alert(f"Data load variance: {variance_pct:.2%}")
        return False
    return True

# DI-05: Reconciliation certification
def check_reconciliation_status():
    uncertified = get_arcs_uncertified(material_threshold=100000)
    if uncertified:
        alert(f"{len(uncertified)} material reconciliations uncertified")
        return False
    return True
```

---

### 4. Automated Processing Controls (AP)

| AP ID | Control Name | Automated Test | Data Source | Pass Criteria |
|-------|--------------|----------------|-------------|---------------|
| **AP-01** | Consolidation Complete | Consolidation runs without error | FCCS consolidation log | Zero consolidation failures |
| **AP-02** | Translation Accurate | Translation rates applied correctly | FCCS translation log | Rate table validation passed |
| **AP-03** | Allocation Balanced | Allocations sum to 100% | PCM allocation trace | Allocation in = allocation out |
| **AP-04** | Tax Calculation | Tax provision calculated per rules | TRCS provision detail | Calculation matches expected |

---

## SOX Reporting Automation

### Monthly SOX Dashboard

```yaml
Dashboard Components:
  Period: "YYYY-MM"
  Close_Date: "YYYY-MM-DD"
  
  Access_Controls:
    New_Users: N
    Terminations_Pending: M
    Admin_Changes: X
    SOD_Violations: 0
    Status: "GREEN / YELLOW / RED"
  
  Change_Controls:
    EDM_Changes: N (100% approved)
    FCCS_Rule_Changes: M (100% tested)
    Emergency_Changes: X (< 5%)
    Post_Close_Changes: 0
    Status: "GREEN / YELLOW / RED"
  
  Data_Integrity:
    Data_Loads: N (X errors, all resolved)
    Manual_JEs: M (100% approved)
    IC_Mismatches: X (< threshold)
    Rec_Certification: "Y% (target: 100%)"
    Status: "GREEN / YELLOW / RED"
  
  Processing_Controls:
    Consolidation_Status: "COMPLETE / FAILED"
    Translation_Status: "VALIDATED"
    Allocation_Status: "BALANCED"
    Tax_Status: "REVIEWED"
    Status: "GREEN / YELLOW / RED"

Overall_Control_Status: "GREEN / YELLOW / RED"
```

### Exception Reporting

Any control failure triggers immediate email + dashboard alert:

```json
{
  "alert_type": "SOX_CONTROL_FAILURE",
  "control_id": "DI-05",
  "control_name": "Reconciliation Complete",
  "severity": "HIGH",
  "period": "2026-02",
  "details": {
    "material_accounts_uncertified": 3,
    "accounts": [
      {"account": "1210.00", "balance": 2500000, "days_uncertified": 2},
      {"account": "2100.00", "balance": 1800000, "days_uncertified": 1},
      {"account": "4100.00", "balance": 3200000, "days_uncertified": 5}
    ]
  },
  "remediation_required": true,
  "notification_sent_to": ["controller@company.com", "sox@company.com"]
}
```

---

## Evidence Package Automation

### Pre-Close Package (Generated Daily During Close)

```
SOX_Evidence_YYYY-MM-DD/
├── 01_Access_Controls/
│   ├── user_access_report.pdf
│   ├── privileged_access_review.pdf
│   └── sod_matrix_validation.pdf
├── 02_Change_Controls/
│   ├── edm_change_log.pdf
│   ├── fccs_rule_changes.pdf
│   └── emergency_change_justification.pdf
├── 03_Data_Integrity/
│   ├── data_load_validation.xlsx
│   ├── manual_je_register.pdf
│   ├── ic_matching_report.pdf
│   └── reconciliation_status.pdf
└── 04_Processing_Controls/
    ├── consolidation_log.pdf
    ├── translation_validation.pdf
    └── pcm_allocation_trace.pdf
```

---

## Quarterly External Audit Support

### Auditor Request Automation

| Typical Auditor Request | Automated Response | Source Data |
|------------------------|-------------------|-------------|
| "Show all users who can post journals" | Security filter extract | FCCS + OCI IAM |
| "Prove all manual JEs were approved" | JE register with approval | FCCS journals |
| "Show all changes to the Chart of Accounts" | EDM hierarchy audit | EDM request history |
| "Prove reconciliations were done before close" | Reconciliation timeline | ARCS status log |
| "Show who has administrative access" | Admin group membership | All apps + OCI |

---

## Implementation Priority

| Priority | Control Area | Effort | Impact |
|----------|--------------|--------|--------|
| **P1** | Data Integrity (DI) | Medium | High - Prevents material errors |
| **P1** | Access Controls (AC) | Low | High - Foundational |
| **P2** | Change Management (CM) | Medium | Medium - Process compliance |
| **P2** | Reconciliation (ARCS) | Low | High - Close critical |
| **P3** | Automated Processing | High | Medium - Efficiency |

---

## Next Steps

1. **Validate control mapping** with Internal Audit
2. **Identify materiality thresholds** ($ amounts, account lists)
3. **Set up automated extraction** for P1 controls
4. **Create exception workflow** (who gets alerted, SLA)
5. **Test with Internal Audit** before external audit season

---

*Document Version: 1.0*
*SOX Framework: PCAOB AS 2201*
*Last Updated: 2026-02-26*
