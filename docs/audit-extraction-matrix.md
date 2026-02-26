# EPM System Administration Audit Extraction Matrix

*Complete reference of system-level audit data for IT security and infrastructure compliance*

---

## 1. Identity & Access Management (IAM)

### User Lifecycle Management

| Artifact | Data Source | Extraction Method | Frequency | Audit Purpose |
|----------|-------------|-------------------|-----------|---------------|
| **User Provisioning Log** | OCI IAM + EPM Security | OCI Audit API / EPM Security API | Daily/Real-time | Detect unauthorized account creation |
| **User Deprovisioning Log** | OCI IAM + HR Feed | OCI Audit API + HR Comparison | Daily/Real-time | Orphan account detection (terminated users with access) |
| **User Modification History** | OCI IAM | OCI Audit API (UpdateUser events) | Daily | Privilege escalation tracking |
| **Last Login Activity** | OCI IAM Sign-In | OCI Sign-In Events | Daily | Dormant account identification |
| **MFA Enrollment Status** | OCI IAM | Identity API | Weekly | Compliance with MFA policy |
| **Password/Key Rotation** | OCI IAM | Audit events (CreateApiKey, DeleteAuthToken, etc.) | Daily | Credential hygiene monitoring |

### Group & Role Management

| Artifact | Data Source | Extraction Method | Frequency | Audit Purpose |
|----------|-------------|-------------------|-----------|---------------|
| **Group Membership Changes** | OCI IAM | Audit API (AddUserToGroup, RemoveUserFromGroup) | Real-time | Privileged access changes |
| **Custom Role Definitions** | OCI IAM Policies | Policy API + Audit | Weekly | Principle of least privilege review |
| **Service Account Inventory** | OCI IAM | User API (filter by type) | Weekly | Service account governance |
| **Cross-Tenancy Access** | OCI IAM | Policy analysis | Weekly | External access review |

### EPM Application Security

| Artifact | Data Source | Extraction Method | Frequency | Audit Purpose |
|----------|-------------|-------------------|-----------|---------------|
| **EPM Role Assignments** | EPM Security (all apps) | REST API `/security/roles` | Weekly | Role-to-user mapping |
| **Security Filter Changes** | FCCS/PBCS | Security API + Audit | Weekly | Data access restrictions |
| **Approvals Workflow Config** | All EPM apps | Admin API | Weekly | Delegation of authority changes |
| **SSO Configuration** | OCI IAM Federation | IAM Policies + Audit | Monthly | Identity provider changes |

---

## 2. Infrastructure & Environment Management

### EPM Instance Lifecycle

| Artifact | Data Source | Extraction Method | Frequency | Audit Purpose |
|----------|-------------|-------------------|-----------|---------------|
| **Instance Creation/Deletion** | OCI Audit + EPM Console | OCI Audit API | Real-time | Unauthorized environment provisioning |
| **Instance Scaling Events** | OCI Compute | Audit API | Weekly | Resource utilization tracking |
| **Instance Configuration Changes** | EPM Settings | EPM Admin API | Daily | Environment drift detection |
| **Maintenance Windows** | OCI Notifications + EPM Status | API + Email parsing | Per event | Planned vs. unplanned changes |
| **Backup Configuration** | OCI Block Storage + EPM | Volume API + EPM Settings | Weekly | RPO/RTO compliance |
| **Disaster Recovery Setup** | OCI Regions + EPM | Multi-region audit | Monthly | DR readiness validation |

### Network & Connectivity

| Artifact | Data Source | Extraction Method | Frequency | Audit Purpose |
|----------|-------------|-------------------|-----------|---------------|
| **Security Group Rules** | OCI Networking | Audit API + Network API | Weekly | Firewall rule changes |
| **VPN/IPSec Configuration** | OCI Networking | Network API | Weekly | Remote access security |
| **Private Endpoint Changes** | OCI Networking | Audit API | Weekly | Data exfiltration risk |
| **Load Balancer Config** | OCI Load Balancer | API + Audit | Monthly | High availability settings |
| **DNS Configuration** | OCI DNS | Audit API | Monthly | Domain/security validation |

### Integration Endpoints

| Artifact | Data Source | Extraction Method | Frequency | Audit Purpose |
|----------|-------------|-------------------|-----------|---------------|
| **Data Exchange Configuration** | EDMCS/FCCS | Admin API | Weekly | Integration point security |
| **EPM Automate Agent Status** | Agent Registration | Agent API | Daily | Automation infrastructure health |
| **ODI/ETL Configuration** | Data Integration | Repository API | Weekly | Data pipeline audit |
| **API Gateway Settings** | OCI API Gateway | API + Audit | Weekly | External API exposure |
| **Webhook Configurations** | EPM Notifications | Configuration export | Weekly | Outbound call monitoring |

---

## 3. Change Management & Configuration

### Application Configuration

| Artifact | Data Source | Extraction Method | Frequency | Audit Purpose |
|----------|-------------|-------------------|-----------|---------------|
| **Dimension/Metadata Changes** | EDM | Request API + Audit | Daily | Master data governance |
| **Business Rule Updates** | FCCS/PBCS | Rules API + Versioning | Daily | Calculation logic changes |
| **Form/Grid Modifications** | PBCS/FCCS | Form API + Audit | Weekly | UI/Input control changes |
| **Report Definition Changes** | All EPM | Report API | Weekly | Financial reporting changes |
| **Task List Updates** | FCCS | Task Manager API | Weekly | Close procedure changes |
| **Currency Rate Tables** | FCCS/PBCS | Rate API | Daily (month-end) | FX rate governance |
| **Substitution Variables** | All EPM | Variable API | Weekly | Cross-app configuration |

### System Configuration

| Artifact | Data Source | Extraction Method | Frequency | Audit Purpose |
|----------|-------------|-------------------|-----------|---------------|
| **System Setting Changes** | EPM Console | Settings API | Daily | Global configuration drift |
| **Email/Notification Config** | EPM Notifications | Notification API | Weekly | Communication audit |
| **Audit Retention Settings** | EPM Security | Admin API | Monthly | Compliance retention |
| **Session Timeout Policies** | OCI IAM + EPM | Policy API | Monthly | Security hardening |
| **Encryption Configuration** | OCI KMS + EPM | KMS API + EPM Settings | Monthly | Data protection validation |

---

## 4. Security & Compliance Monitoring

### Access Control Monitoring

| Artifact | Data Source | Extraction Method | Frequency | Audit Purpose |
|----------|-------------|-------------------|-----------|---------------|
| **Failed Login Attempts** | OCI IAM + EPM | Audit API + Sign-In logs | Real-time | Brute force detection |
| **Elevated Privilege Usage** | OCI IAM | Audit API (admin actions) | Daily | Privileged access monitoring |
| **After-Hours Access** | OCI IAM + EPM | Sign-In logs | Daily | Anomalous access patterns |
| **Geographic Access Anomalies** | OCI IAM | Sign-In logs | Daily | Impossible travel detection |
| **Concurrent Session Analysis** | OCI IAM | Session API | Daily | Account sharing detection |
| **API Key Usage Patterns** | OCI IAM | Audit API | Weekly | Key exfiltration detection |

### Data Security

| Artifact | Data Source | Extraction Method | Frequency | Audit Purpose |
|----------|-------------|-------------------|-----------|---------------|
| **Data Export Activities** | Data Management | Export API + Audit | Daily | Unauthorized data extraction |
| **Bulk Data Downloads** | Smart View / REST | API + Access logs | Daily | Data leakage detection |
| **Snapshot/Backup Access** | OCI Object Storage | Access logs | Weekly | Backup data access |
| **Cross-Border Data Transfer** | OCI Audit | Audit events | Weekly | GDPR/data residency |
| **Data Masking Configuration** | EPM Test environments | Admin API | Monthly | PII protection |

### Compliance Artifacts

| Artifact | Data Source | Extraction Method | Frequency | Audit Purpose |
|----------|-------------|-------------------|-----------|---------------|
| **SOC2 Evidence** | OCI/Epm | Compliance API | Quarterly | Control evidence export |
| **ISO 27001 Artifacts** | Security Config | Configuration export | Quarterly | Standard compliance |
| **License Utilization** | OCI/Epm | Usage API | Monthly | License compliance |
| **Vendor Access Reviews** | Third-party integrations | Integration audit | Quarterly | Supplier risk |
| **Certificate Expiration** | OCI Certificates | Certificate API | Weekly | TLS/SSL validity |

---

## 5. Operations & Monitoring

### System Health & Performance

| Artifact | Data Source | Extraction Method | Frequency | Audit Purpose |
|----------|-------------|-------------------|-----------|---------------|
| **System Availability Metrics** | OCI Monitoring | Metrics API | Daily | SLA compliance |
| **Performance Degradation Events** | EPM Health Check | Status API | Real-time | Capacity planning |
| **Resource Utilization Trends** | OCI Monitoring | Compute/Storage metrics | Weekly | Cost optimization |
| **Error Log Analysis** | EPM System Logs | Log export / API | Daily | Incident root cause |
| **Job Queue Status** | EPM Background Jobs | Job API | Daily | Batch processing audit |
| **Long-Running Operations** | EPM Job History | Job API | Daily | Performance baseline |

### Incident Management

| Artifact | Data Source | Extraction Method | Frequency | Audit Purpose |
|----------|-------------|-------------------|-----------|---------------|
| **Incident Tickets** | ServiceNow/Jira | API integration | Real-time | Change correlation |
| **Emergency Changes** | EPM/OCI | Audit API (flagged events) | Real-time | Emergency change tracking |
| **Rollback Events** | EPM Versioning | Version API | Per event | Failed change recovery |
| **Service Degradation** | OCI Status + EPM | Status page + API | Per event | Outage documentation |

---

## 6. Audit & Logging Infrastructure

### Log Management

| Artifact | Data Source | Extraction Method | Frequency | Audit Purpose |
|----------|-------------|-------------------|-----------|---------------|
| **OCI Audit Log Retention** | OCI Logging | Logging API | Weekly | Retention compliance |
| **EPM Audit Trail Completeness** | EPM Security | Audit API sampling | Weekly | Log integrity check |
| **Log Forwarding Status** | OCI Logging / SIEM | Service configuration | Daily | Centralized logging |
| **Log Access Patterns** | OCI IAM | Audit API | Weekly | Privileged log access |
| **Log Tampering Detection** | OCI Audit | Integrity checks | Weekly | Audit log protection |

### Audit Automation

| Artifact | Data Source | Extraction Method | Frequency | Audit Purpose |
|----------|-------------|-------------------|-----------|---------------|
| **Extraction Job Logs** | This automation | Internal logging | Every run | Automation audit trail |
| **Dashboard Access** | SpudHub/OCI | Access logs | Weekly | Audit tool usage |
| **Alert Acknowledgment** | Notification Systems | Alert API | Real-time | SOX exception workflow |
| **Report Distribution** | Email/System | Distribution logs | Weekly | Evidence chain custody |

---

## Extraction Summary by Priority

### Tier 1: Real-Time / Daily (Critical for Security)
1. **IAM Events**: User provisioning/deprovisioning, group changes, MFA enrollments
2. **Failed Access**: Login failures, privilege escalation attempts
3. **Instance Changes**: Create/Delete EPM instances, scaling events
4. **Emergency Changes**: Critical configuration modifications
5. **Extraction Health**: Automation job status

### Tier 2: Weekly (Operational)
1. **Access Reviews**: Full user/group inventory, dormant accounts
2. **Configuration Drift**: Security settings, network rules
3. **Role Assignments**: Permission recertification
4. **Resource Utilization**: Cost optimization, capacity planning
5. **Certificate Validity**: Expiration monitoring

### Tier 3: Monthly/Quarterly (Compliance)
1. **SOX Evidence Package**: Aggregated control evidence
2. **License Compliance**: Usage vs. entitlement
3. **Disaster Recovery**: DR configuration validation
4. **Vendor Access**: Third-party integration review
5. **Policy Effectiveness**: IAM policy optimization

---

## Recommended Data Retention

| Data Type | Security Requirement | Recommendation |
|-----------|---------------------|----------------|
| IAM Audit Logs | 1 year minimum | 2+ years (store in OCI Object Storage) |
| Login Activity | 90 days standard | 1+ year for security analysis |
| Configuration Changes | 7 years (if SOX) | 7+ years with versioning |
| System Performance Metrics | 30 days operational | 1+ year for trending |
| Incident Records | Permanent | Permanent with attachments |
| Automation Logs | 1 year | 2+ years for troubleshooting |

---

## Next Steps

1. **Prioritize Tier 1 extractions** for immediate security benefit
2. **Set up real-time alerting** for IAM events to security team
3. **Create weekly access review** report for managers
4. **Build SOX evidence package** automation for quarterly compliance
5. **Integrate with SIEM** for centralized security monitoring

---

*Document Version: 2.0 (System Admin Focus)*
*Last Updated: 2026-02-26*
*Owner: IT Security & Infrastructure Team*
