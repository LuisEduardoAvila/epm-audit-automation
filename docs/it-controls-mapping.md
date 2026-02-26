# IT System Controls Mapping for EPM Infrastructure

*Maps system administration activities to IT audit control frameworks*

---

## Control Framework Alignment

| Internal Control | COBIT 2019 | NIST 800-53 | ISO 27001 | Purpose |
|------------------|------------|-------------|-----------|---------|
| Access Management | DSS05.04 | AC-2, AC-3 | A.9.1 | User lifecycle |
| Change Management | APO12.02 | CM-3, CM-4 | A.12.1.2 | Controlled changes |
| Configuration Mgmt | BAI09.01 | CM-8 | A.12.1.1 | Asset inventory |
| Monitoring | DSS05.07 | AU-3, AU-6 | A.12.4 | Security monitoring |
| Backup/Recovery | DSS04.07 | CP-9, CP-10 | A.12.3.1 | Resilience |
| Privileged Access | DSS05.04 | AC-6 | A.9.2.3 | Least privilege |

---

## 1. Identity & Access Management Controls (IAM)

### IAM-01: User Account Lifecycle Management

| Control Element | Automated Test | Data Source | Pass Criteria |
|----------------|---------------|-------------|---------------|
| **Provisioning** | New accounts have approved tickets | OCI Audit + ServiceNow | All CreateUser events linked to ticket |
| **Deprovisioning** | Terminated users disabled within 24h | HR Feed vs IAM | Zero terminated users with active access > 24h |
| **Reauthentication** | Inactive accounts suspended | OCI Sign-In logs | Accounts > 90d inactive flagged |
| **MFA Enforcement** | MFA active on all accounts | OCI IAM API | 100% MFA enrollment |
| **Privileged Review** | Admin accounts reviewed quarterly | Group membership audit | Quarterly attestation on file |

**Daily Automated Check:**
```python
def check_user_lifecycle():
    # Check 1: Orphan accounts
    terminated_but_active = get_users_active_in_iam() - get_active_employees()
    alert_if(terminated_but_active, severity="CRITICAL")
    
    # Check 2: New accounts without tickets
    recent_users = get_users_created_since(yesterday)
    for user in recent_users:
        if not has_approval_ticket(user):
            alert(user, "Unapproved account creation")
    
    # Check 3: MFA compliance
    users_without_mfa = get_users_without_mfa()
    if users_without_mfa:
        alert(f"{len(users_without_mfa)} users without MFA")
```

---

### IAM-02: Privileged Access Management

| Control Element | Automated Test | Data Source | Pass Criteria |
|----------------|---------------|-------------|---------------|
| **Admin Role Assignment** | All admin assignments approved | Audit logs | SOX approval for admin access |
| **Just-in-Time Access** | Standing admin rights minimized | Privileged Access Workflows | < 5% standing admin accounts |
| **Session Recording** | Privileged sessions logged | Session audit | 100% admin session capture |
| **Seperation of Duties** | No conflicting role assignments | Custom SOD matrix | Zero SOD violations |

**EPM Privileged Roles to Monitor:**
- Service Administrator (all apps)
- Identity Domain Administrator (OCI)
- Network Administrator (OCI)
- Security Administrator (OCI)
- Database Administrator (Autonomous)
- Object Storage Administrator
- Key Administrator (KMS)

---

### IAM-03: Service Account Governance

| Control Element | Automated Test | Data Source | Pass Criteria |
|----------------|---------------|-------------|---------------|
| **Inventory** | All service accounts documented | IAM API | 100% service accounts cataloged |
| **Rotation** | Keys/tokens rotated every 90 days | Audit API (CreateApiKey events) | Zero keys > 90 days old |
| **Scope** | Service accounts have minimal permissions | Policy analysis | No broad permissions |
| **Monitoring** | Service account usage monitored | Audit logs | Anomaly detection active |

---

## 2. Change Management Controls

### CM-01: Controlled Change Process

| Control Element | Automated Test | Data Source | Pass Criteria |
|----------------|---------------|-------------|---------------|
| **Change Tickets** | All changes have tickets | Audit + ServiceNow/Jira | 100% change correlation |
| **Approval Evidence** | Changes approved before implementation | Approval workflow | Approval timestamp < implementation |
| **Testing Evidence** | Changes tested in non-prod | Environment comparison | Test environment validation |
| **Rollback Plan** | Rollback procedure documented | Change ticket fields | Rollback plan exists |
| **Implementation** | Changes during maintenance windows | Timestamp analysis | > 95% during approved windows |

**Change Categories:**
```yaml
Standard Changes:
  - EDM hierarchy updates (via workflow)
  - Monthly rate table updates
  - User provisioning
  - Scheduled backups

Normal Changes:
  - Dimension structure modifications
  - Business rule updates
  - Security filter changes
  - Integration modifications

Emergency Changes:
  - Security vulnerability patching
  - Critical system recovery
  - Immediate access grants
  
Emergency Threshold: < 5% of all changes
```

---

### CM-02: Configuration Drift Detection

| Control Element | Automated Test | Data Source | Pass Criteria |
|----------------|---------------|-------------|---------------|
| **Baseline Comparison** | Weekly config vs. approved baseline | Config dumps | Zero drift > threshold |
| **Unauthorized Changes** | Changes outside tickets flagged | Audit correlation | All drift explained |
| **Emergency Changes** | Emergency changes documented | Change categorization | Emergency < 5%, all justified |

**Critical Configurations to Baseline:**
- EPM application security settings
- OCI IAM policies
- Network security groups
- Encryption key configurations
- Audit retention settings
- Session timeout policies
- Notification configurations

---

## 3. Infrastructure & Operations

### OP-01: Environment Management

| Control Element | Automated Test | Data Source | Pass Criteria |
|----------------|---------------|-------------|---------------|
| **Separation** | Prod/Non-prod properly isolated | Network rules + IAM | No cross-environment access |
| **Naming Convention** | Resources follow standards | Resource inventory | 100% naming compliance |
| **Tagging** | All resources tagged (owner, cost center) | Resource API | 100% tagged |
| **Sunsetting** | Decommissioned resources removed | Resource lifecycle | No orphaned resources > 30 days |

### OP-02: Capacity Management

| Control Element | Automated Test | Data Source | Pass Criteria |
|----------------|---------------|-------------|---------------|
| **Utilization** | Resource usage within thresholds | OCI Monitoring | > 70% = capacity planning |
| **Scaling Events** | Auto-scaling properly configured | Compute API | Scaling policies active |
| **Storage Growth** | Data growth trends tracked | Storage metrics | > 80% = upgrade planned |
| **Performance** | Response times within SLA | APM metrics | < 3s query response |

### OP-03: Backup & Recovery

| Control Element | Automated Test | Data Source | Pass Criteria |
|----------------|---------------|-------------|---------------|
| **Backup Execution** | Backups complete successfully | OCI Block Volume API | 100% success rate |
| **Backup Validation** | Backups are restorable | Test restore logs | Monthly restore test |
| **Retention Compliance** | Retention periods met | Backup policy | 7-year retention for SOX |
| **Encryption** | Backups encrypted at rest | KMS API | All backups encrypted |
| **Offsite/DR** | DR copies exist in secondary region | Cross-region validation | DR copies current |

---

## 4. Security Monitoring Controls

### SEC-01: Security Event Monitoring

| Control Element | Automated Test | Data Source | Pass Criteria |
|----------------|---------------|-------------|---------------|
| **Log Collection** | All critical logs forwarded | Logging service API | 100% log forwarding |
| **Alert Coverage** | Critical events generate alerts | SIEM/Notification | Real-time alerting |
| **Response Time** | Security events acknowledged | Incident management | < 4h for critical |
| **False Positive** | Alert tuning reduces noise | Alert history | < 20% false positive |

**Critical Events Requiring Immediate Alert:**
```yaml
Real-Time Alerts:
  - Failed login > 5 attempts within 5 minutes (same user)
  - Failed login > 10 attempts within 5 minutes (any user)
  - Privilege escalation (admin role assigned)
  - New privileged account created
  - EPM instance created/deleted
  - API key created by non-service-account
  - Access from new country/region
  - After-hours access by privileged user
  - Data export > threshold
  - Emergency change without ticket

Daily Alerts:
  - Configuration drift detected
  - Orphan user accounts
  - Keys expiring within 30 days
  - Failed backup
  - Long-running stuck jobs
  - License utilization > 90%
```

---

### SEC-02: Vulnerability Management

| Control Element | Automated Test | Data Source | Pass Criteria |
|----------------|---------------|-------------|---------------|
| **Scan Coverage** | All systems scanned regularly | Vulnerability scanner | 100% scan coverage |
| **Critical Findings** | Critical vulns remediated fast | Scan results | < 7 days for critical |
| **Patch Compliance** | Patches applied within SLA | Patch management | > 95% compliance |
| **Exception Tracking** | Risk exceptions documented | Exception register | All exceptions approved |

### SEC-03: Data Protection

| Control Element | Automated Test | Data Source | Pass Criteria |
|----------------|---------------|-------------|---------------|
| **Encryption at Rest** | All data encrypted | KMS + Storage API | 100% encryption coverage |
| **Encryption in Transit** | TLS enforced | Load balancer + API Gateway | TLS 1.2+ minimum |
| **Key Rotation** | Keys rotated per policy | KMS API | Annual rotation |
| **Data Masking** | Non-prod data masked | Data classification | PII masked in lower environments |

---

## 5. Compliance & Audit

### COM-01: Audit Trail Integrity

| Control Element | Automated Test | Data Source | Pass Criteria |
|----------------|---------------|-------------|---------------|
| **Log Immutability** | Audit logs protected from tamper | OCI Logging integrity | Immutable logging |
| **Retention** | Logs retained per policy | Logging configuration | SOX: 7 years |
| **Access Controls** | Log access restricted | IAM policies | Only security team + auditors |
| **Extraction Audit** | All audit extractions logged | Automation logs | Complete extraction chain |

### COM-02: Evidence Management

| Control Element | Automated Test | Data Source | Pass Criteria |
|----------------|---------------|-------------|---------------|
| **Chain of Custody** | Evidence handling documented | Extraction logs | Complete custody chain |
| **Evidence Completeness** | All required evidence collected | Checklist validation | 100% required artifacts |
| **Distribution Control** | Evidence access tracked | Distribution logs | Authorized access only |

---

## Control Testing Automation

### Daily System Health Dashboard

```yaml
Dashboard_Name: "EPM_Security_Controls_Dashboard"
Generated: "Daily at 06:00 UTC"

Section_Access_Management:
  Overall_Control_Status: "GREEN/YELLOW/RED"
  
  Users_Provisioned_Last_24h: 5
  Users_Deprovisioned_Last_24h: 3
  Orphan_Dormant_Accounts: 0
  MFA_Compliance: "100%"
  Admin_Changes: 2
  Service_Account_Key_Rotations: 1
  
  Status: "GREEN"

Section_Change_Management:
  Changes_Last_24h: 12
  Emergency_Changes: 0
  Changes_Without_Tickets: 0
  Configuration_Drift: "None"
  
  Status: "GREEN"

Section_Infrastructure:
  Backup_Success_Rate: "100%"
  DR_Replication_Status: "Current"
  Certificate_Expirations_30d: 0
  Resource_Tagging_Compliance: "98%"
  
  Status: "GREEN"

Section_Security_Monitoring:
  Failed_Login_Attempts: 45
  Privilege_Escalation_Events: 0
  Suspicious_Access_Patterns: 0
  Data_Export_Events: 3
  
  Status: "GREEN"

Overall_Security_Posture: "GREEN"
Exceptions_Requires_Review: []
Next_Review_Date: "2026-03-01"
```

### Weekly Control Attestation

**Manager Review Package:**
```
EPM_Controls_Week_2026-W09/
├── 01_Access_Management/
│   ├── user_provisioning_log.csv
│   ├── orphan_account_report.pdf
│   ├── admin_change_approval.pdf
│   └── attestation_signoff.pdf
├── 02_Change_Management/
│   ├── change_log_with_tickets.csv
│   ├── emergency_change_justification.pdf
│   └── configuration_drift_report.pdf
├── 03_Infrastructure/
│   ├── backup_success_report.pdf
│   ├── capacity_utilization.pdf
│   └── certificate_expiry_report.pdf
└── 04_Security/
    ├── failed_login_analysis.pdf
    ├── privilege_usage_report.pdf
    └── data_export_audit.pdf
```

---

## Exception Management

### Exception Tracking

When automated testing finds a control failure, it creates an exception ticket:

```json
{
  "exception_id": "EPM-2026-0226-001",
  "control_framework": "IAM-01",
  "control_name": "User Account Lifecycle",
  "findings": {
    "orphan_accounts": 2,
    "accounts": [
      {
        "user_id": "ocid1.user.oc1..xxx",
        "username": "john.smith",
        "termination_date": "2026-02-20",
        "days_since_termination": 6,
        "active_in_epm": true,
        "active_in_oci": true,
        "last_login": "2026-02-15"
      }
    ]
  },
  "severity": "HIGH",
  "sla_hours": 24,
  "assigned_to": "iam-team@company.com",
  "escalation": "security@company.com",
  "auto_remediable": true,
  "remediation_script": "disable_user.sh"
}
```

---

## Implementation Roadmap

| Phase | Duration | Focus | Deliverables |
|-------|----------|-------|--------------|
| **1** | Weeks 1-2 | Foundation | IAM extraction, OCI audit logs, basic alerting |
| **2** | Weeks 3-4 | Change Control | Change management tracking, configuration baselines |
| **3** | Weeks 5-6 | Operations | Backup monitoring, capacity reports, DR validation |
| **4** | Weeks 7-8 | Security | SIEM integration, advanced threat detection |
| **5** | Weeks 9-12 | Compliance | SOX evidence packaging, manager attestation automation |

---

*Document Version: 2.0 (IT Controls Focus)*
*Frameworks: COBIT 2019, NIST 800-53 Rev 5, ISO 27001:2022*
*Last Updated: 2026-02-26*
*Owner: IT Security & Infrastructure Team*
