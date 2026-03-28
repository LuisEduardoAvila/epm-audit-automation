# Specification: EPM Audit CLI

## Requirements

### REQ-001: Authentication & Connection

**As a** SOX auditor  
**I want** secure authentication to EPM Cloud instances  
**So that** I can extract audit evidence without storing credentials in scripts

#### Scenarios

##### SC-001: OAuth 2.0 Authentication

**Given** an EPM Cloud instance configured in `applications.yaml`  
**When** I run `epm login fccs_prod`  
**Then** the CLI retrieves OAuth token from configured identity provider  
**And** caches token for subsequent commands  
**And** refreshes token automatically before expiry

**Edge Cases:**
- Token expires mid-session → Auto-refresh, retry command
- OAuth service unavailable → Error with retry suggestion
- Invalid client credentials → Clear error, check OCI Vault

##### SC-002: Connection Verification

**Given** valid authentication credentials  
**When** I run `epm login fccs_prod --verify`  
**Then** the CLI tests connection with a lightweight API call  
**And** reports instance version and available endpoints

**Edge Cases:**
- Instance unreachable → Network error with troubleshooting steps
- API version mismatch → Warning about compatibility
- Insufficient permissions → List required roles

---

### REQ-002: Artifact Change Tracking

**As a** SOX auditor  
**I want** to query configuration changes within a date range  
**So that** I can identify material changes for audit evidence

#### Scenarios

##### SC-003: List Artifact Changes

**Given** valid authentication to an FCCS instance  
**When** I run `epm artifact-changes --app fccs_prod --from 2026-03-01 --to 2026-03-27`  
**Then** the CLI calls `/applications/{app}/artifact-modification` API  
**And** returns changes filtered by date range  
**And** classifies each change as material or operational

**Edge Cases:**
- No changes in range → Empty result with "No changes found" message
- Large result set → Pagination support with `--limit` and `--offset`
- Rate limiting → Exponential backoff with progress indicator
- Permission denied → Clear error with required role list

##### SC-004: Filter by Artifact Type

**Given** valid authentication  
**When** I run `epm artifact-changes --app fccs_prod --type CONSOLIDATION_RULE --from 2026-03-01`  
**Then** the CLI filters results to specified artifact type  
**And** supports multiple types with `--type RULE,FORM,DIMENSION`

**Edge Cases:**
- Invalid artifact type → List valid types for the application
- Type not applicable to app → Warning with app-specific types

##### SC-005: Filter by User

**Given** valid authentication  
**When** I run `epm artifact-changes --app fccs_prod --modified-by john.smith --from 2026-03-01`  
**Then** the CLI filters results to changes by specific user  
**And** supports `--modified-by-exclude` to filter out service accounts

**Edge Cases:**
- User not found → Empty result with suggestion to check spelling
- Service account flood → Suggest `--modified-by-exclude svc_*`

##### SC-006: Material Change Classification

**Given** artifact change records from API  
**When** the CLI processes each record  
**Then** configuration changes are marked as `MATERIAL`  
**And** operational changes are marked as `OPERATIONAL`  
**And** classification follows the type mapping from `extract-artifact-changes.py`

**Classification Rules:**
| Type | Classification |
|------|---------------|
| CONSOLIDATION_RULE | MATERIAL |
| BUSINESS_RULE | MATERIAL |
| DATA_FORM | MATERIAL |
| DIMENSION | MATERIAL |
| PERIOD_STATUS | OPERATIONAL |
| JOB_EXECUTION | OPERATIONAL |
| SNAPSHOT | OPERATIONAL |

**Edge Cases:**
- Unknown artifact type → Flag for manual review
- Hybrid changes (config + state) → Mark as MATERIAL if any config field changed

---

### REQ-003: EDM Request History

**As a** data governance analyst  
**I want** to retrieve EDM request history  
**So that** I can audit metadata deployment approvals

#### Scenarios

##### SC-007: List EDM Requests

**Given** valid authentication to an EDM instance  
**When** I run `epm edm-requests --app edm_prod --status COMPLETED --from 2026-03-01`  
**Then** the CLI calls `/edm/rest/v1/requests` API  
**And** returns requests matching the filter  
**And** includes deployment status for each request

**Edge Cases:**
- No requests match → Empty result with date range suggestion
- Pending requests → Include in output with status indicator
- Large result set → Pagination with progress indicator

##### SC-008: Get Request Details

**Given** valid authentication  
**When** I run `epm edm-request --app edm_prod --id REQ-2026-0226-001`  
**Then** the CLI calls `/edm/rest/v1/requests/{id}` API  
**And** returns full request details including all items  
**And** shows before/after values for each changed attribute

**Edge Cases:**
- Request not found → Error with suggestion to check ID format
- Request still pending → Warning that details may change
- Complex item list → Pretty-print with truncation option

##### SC-009: List Policy Violations

**Given** valid authentication  
**When** I run `epm edm-violations --app edm_prod --from 2026-03-01`  
**Then** the CLI calls `/edm/rest/v1/policies/violations` API  
**And** returns governance violations  
**And** includes severity and remediation status

**Edge Cases:**
- No violations → "No violations found" message
- Violations resolved → Include with RESOLVED status
- Permission denied → Error with required role (Data Steward)

---

### REQ-004: Business Rule Inspection

**As a** SOX auditor  
**I want** to extract business rule definitions  
**So that** I can compare current logic against baselines

#### Scenarios

##### SC-010: List Business Rules

**Given** valid authentication to a Planning (PBCS) instance  
**When** I run `epm rules --app pbcs_prod`  
**Then** the CLI calls `/HyperionPlanning/rest/v3/applications/{app}/calculations` API  
**And** returns list of rules with metadata  
**And** includes last modified date and user

**Edge Cases:**
- No rules → Empty result with app validation
- Large rule list → Pagination with `--limit`

##### SC-011: Get Rule Definition

**Given** valid authentication  
**When** I run `epm rule --app pbcs_prod --id Calc_Headcount --output formula.txt`  
**Then** the CLI calls `/HyperionPlanning/rest/v3/applications/{app}/calculations/{id}` API  
**And** extracts formula, member scope, execution order  
**And** writes to file in structured format (JSON or text)

**Edge Cases:**
- Rule not found → Error with suggestion to list rules first
- Large formula → Truncation warning with full content option
- Binary rule → Error explaining limitation (can't extract compiled rules)

##### SC-012: Compare Rules

**Given** valid authentication  
**When** I run `epm rule-diff --app pbcs_prod --id Calc_Headcount --baseline snapshots/baseline.json`  
**Then** the CLI compares current rule definition to baseline  
**And** reports differences in formula, scope, order  
**And** highlights SOX-relevant changes

**Edge Cases:**
- Baseline not found → Error with path suggestion
- Same content → "No differences found" message
- Incompatible baseline version → Warning about version mismatch

---

### REQ-005: OCI Infrastructure Monitoring

**As a** cloud administrator  
**I want** to query OCI infrastructure status  
**So that** I can verify environment health for audit

#### Scenarios

##### SC-013: List OCI Compute Instances

**Given** valid OCI API key authentication  
**When** I run `epm oci-instances --compartment ocid1.compartment.xxx`  
**Then** the CLI calls OCI Compute API  
**And** returns list of instances with status  
**And** filters to EPM-related instances by tag

**Edge Cases:**
- OCI CLI not configured → Setup instructions
- No instances → Empty result
- Permission denied → Required policy list

##### SC-014: OCI Storage Usage

**Given** valid OCI authentication  
**When** I run `epm oci-storage --bucket epm-backups`  
**Then** the CLI calls OCI Object Storage API  
**And** returns bucket size and object count  
**And** shows retention policy status

**Edge Cases:**
- Bucket not found → Error with compartment buckets list
- Large bucket → Progress indicator during scan

##### SC-015: OCI Network Status

**Given** valid OCI authentication  
**When** I run `epm oci-network --vcn ocid1.vcn.xxx`  
**Then** the CLI calls OCI Networking API  
**And** returns VCN, subnet, security list status  
**And** validates against EPM requirements

**Edge Cases:**
- VCN not found → Error with compartment VCNs list
- Complex network → Summarize with detail option

---

### REQ-006: IAM / IDCS User & Group Management

**As a** SOX auditor  
**I want** to retrieve user and group information from IDCS/OCI IAM  
**So that** I can perform access reviews and detect security risks

#### Scenarios

##### SC-024: List IAM Users

**Given** valid OCI authentication  
**When** I run `epm iam-users --compartment ocid1.compartment.xxx`  
**Then** the CLI calls OCI Identity API  
**And** returns list of users with metadata  
**And** includes last login timestamp for dormant detection

**Edge Cases:**
- OCI CLI not configured → Setup instructions
- No users → Empty result with compartment validation
- Permission denied → Required policy list

##### SC-025: List IAM Groups

**Given** valid OCI authentication  
**When** I run `epm iam-groups --compartment ocid1.compartment.xxx`  
**Then** the CLI calls OCI Identity API  
**And** returns list of groups with member counts  
**And** identifies privileged groups (Administrators, etc.)

**Edge Cases:**
- Large group list → Pagination with progress indicator
- Nested groups → Flatten or indicate hierarchy

##### SC-026: List Group Memberships

**Given** valid OCI authentication  
**When** I run `epm iam-memberships --compartment ocid1.compartment.xxx`  
**Then** the CLI returns user-group mapping  
**And** shows which users belong to which groups  
**And** supports `--group <name>` to filter specific group

**Edge Cases:**
- No memberships → Empty result
- User in many groups → Summarize with detail option
- Cross-compartment memberships → Indicate scope

##### SC-027: Access Review Report

**Given** valid OCI authentication  
**When** I run `epm iam-access-review --compartment ocid1.compartment.xxx`  
**Then** the CLI generates comprehensive access review  
**And** includes users, service accounts, privileged users, dormant accounts  
**And** includes group assignments and SoD violations  
**And** outputs in SOX audit format

**Report Sections:**
| Section | Content |
|---------|---------|
| Summary | Total counts, key metrics |
| Users | All users with last login |
| Service Accounts | Users matching `epm-*` or `svc-*` patterns |
| Privileged Users | Members of admin groups |
| Dormant Accounts | No login >90 days |
| Group Assignments | User-group matrix |
| SoD Violations | Conflicting role combinations |
| Security Flags | Anomalies, recommendations |

**Edge Cases:**
- No users → Empty report with compartment validation
- No privileged groups → Report all users as non-privileged
- Dormant threshold → Configurable via `--dormant-days`

##### SC-028: Filter Users

**Given** valid OCI authentication  
**When** I run `epm iam-users --compartment <id> --filter service-accounts`  
**Then** the CLI filters to service accounts only  
**And** supports `--filter dormant` for dormant accounts  
**And** supports `--filter privileged` for privileged users  
**And** supports multiple filters with comma separation

**Filter Types:**
| Filter | Criteria |
|--------|----------|
| `service-accounts` | Username starts with `epm-` or `svc-` |
| `dormant` | Last login >90 days |
| `privileged` | Member of admin group |
| `orphan` | No group memberships |

##### SC-029: CSV Export for SOX Review

**Given** any IAM command  
**When** I run with `--output csv --file access-review.csv`  
**Then** the CLI outputs CSV in SOX audit format  
**And** includes required columns (User, Email, Groups, Last Login, Status)  
**And** can be imported to Excel or GRC system

**CSV Format:**
```csv
Username,Email,Groups,Privileged,LastLogin,Status,DormantDays
john.smith@company.com,john.smith@company.com,"Admin,Finance",Yes,2026-03-15,Active,0
svc-automation@company.com,svc-automation@company.com,"ServiceAccounts",No,2026-03-27,Active,0
```

**Edge Cases:**
- User with no email → Empty column
- User with many groups → Comma-separated in quotes
- Unicode characters → UTF-8 encoding

---

### REQ-007: Output Formats

**As a** script developer  
**I want** structured output in multiple formats  
**So that** I can integrate with other tools

#### Scenarios

##### SC-016: JSON Output

**Given** any command  
**When** I run with `--output json`  
**Then** the CLI outputs valid JSON to stdout  
**And** includes all fields from API response  
**And** can be piped to `jq` or other tools

**Edge Cases:**
- Binary data → Base64 encode
- Very large output → Stream mode with `--stream`

##### SC-017: Table Output (Default)

**Given** any command  
**When** I run without format flag  
**Then** the CLI outputs human-readable table  
**And** truncates long fields with `...`  
**And** adjusts column widths to terminal

**Edge Cases:**
- Non-interactive terminal → Default to JSON
- Wide tables → Wrap or truncate intelligently

##### SC-018: CSV Output

**Given** any command  
**When** I run with `--output csv`  
**Then** the CLI outputs CSV with headers  
**And** escapes special characters properly  
**And** can be imported to Excel or database

**Edge Cases:**
- Nested objects → Flatten or JSON column
- Unicode characters → UTF-8 encoding

---

### REQ-007: Command Style Compatibility

**As an** EPM Automate user  
**I want** familiar command patterns  
**So that** I can use existing muscle memory

#### Command Mapping

| EPM Automate Pattern | EPM Audit CLI | Purpose |
|---------------------|---------------|---------|
| `epmautomate login user@domain url` | `epm login <app_id>` | Authenticate |
| `epmautomate logout` | `epm logout` | End session |
| `epmautomate listfiles` | `epm files --list` | List files |
| N/A | `epm artifact-changes` | Gap: change tracking |
| N/A | `epm edm-requests` | Gap: request history |
| N/A | `epm rule-diff` | Gap: rule comparison |
| N/A | `epm oci-instances` | Gap: infrastructure |
| N/A | `epm iam-users` | Gap: IDCS user audit |
| N/A | `epm iam-groups` | Gap: IDCS group audit |
| N/A | `epm iam-access-review` | Gap: SOX access review |

#### Global Flags

| Flag | Purpose | Example |
|------|---------|---------|
| `--app <id>` | Application ID from config | `--app fccs_prod` |
| `--from <date>` | Start date (YYYY-MM-DD) | `--from 2026-03-01` |
| `--to <date>` | End date (YYYY-MM-DD) | `--to 2026-03-27` |
| `--output <fmt>` | Output format (json/table/csv) | `--output json` |
| `--verbose` | Debug logging | `--verbose` |
| `--dry-run` | Show API call without executing | `--dry-run` |

---

### REQ-008: Error Handling

**As a** CLI user  
**I want** clear error messages  
**So that** I can fix problems without support

#### Scenarios

##### SC-019: Authentication Errors

**Given** invalid credentials  
**When** I run any command  
**Then** the CLI shows clear error message  
**And** suggests authentication refresh  
**And** exits with code 401

**Error Messages:**
- `Authentication failed: Check credentials in OCI Vault`
- `Token expired: Run 'epm login <app>' to refresh`
- `Permission denied: Required role 'Service Administrator'`

##### SC-020: Network Errors

**Given** unreachable EPM instance  
**When** I run any command  
**Then** the CLI shows network error  
**And** suggests connectivity checks  
**And** exits with code 503

**Error Messages:**
- `Connection refused: Check if VPN is connected`
- `Timeout: EPM instance may be in maintenance`
- `DNS resolution failed: Check hostname`

##### SC-021: Rate Limiting

**Given** EPM API rate limit exceeded  
**When** I run any command  
**Then** the CLI shows rate limit message  
**And** waits and retries automatically  
**And** exits with code 429 if retries exhausted

**Behavior:**
- First retry: Wait 5 seconds
- Second retry: Wait 15 seconds
- Third retry: Wait 60 seconds
- Fail after 3 retries

##### SC-022: Validation Errors

**Given** invalid command arguments  
**When** I run any command  
**Then** the CLI shows validation error  
**And** shows correct usage  
**And** exits with code 400

**Example:**
```
Error: Invalid date format '2026/03/01'
Usage: epm artifact-changes --app <id> --from YYYY-MM-DD --to YYYY-MM-DD
Example: epm artifact-changes --app fccs_prod --from 2026-03-01 --to 2026-03-27
```

---

### REQ-009: Configuration Integration

**As a** security administrator  
**I want** the CLI to use existing configuration  
**So that** I don't duplicate credential management

#### Scenarios

##### SC-023: Use applications.yaml

**Given** existing `config/applications.yaml`  
**When** I run `epm login fccs_prod`  
**Then** the CLI reads connection URL from config  
**And** uses OAuth scope from config  
**And** retrieves credentials via credential manager

**Integration:**
- App IDs match `applications.yaml` keys
- Token scopes match `oauth` section
- Environment metadata from `environments` section

##### SC-024: Environment Isolation

**Given** multiple environments (prod, test, dev)  
**When** I run commands with different `--app` values  
**Then** the CLI uses correct credentials per environment  
**And** never crosses environment boundaries  
**And** shows current environment in prompt

**Safety:**
- Production apps require `--confirm` for destructive operations
- Test/dev apps have no extra confirmation

---

### REQ-010: CLI Installation & Distribution

**As a** DevOps engineer  
**I want** simple CLI installation  
**So that** I can deploy to audit team machines

#### Scenarios

##### SC-025: pip Install

**Given** Python 3.10+ environment  
**When** I run `pip install epm-audit-cli`  
**Then** the CLI installs with all dependencies  
**And** `epm` command is available in PATH  
**And** configuration is created at `~/.epm-audit/`

**Dependencies:**
- requests >= 2.28
- pyyaml >= 6.0
- click >= 8.0
- rich >= 13.0 (for tables)
- oci >= 2.100 (optional, for OCI commands)

##### SC-026: Configuration Setup

**Given** fresh installation  
**When** I run `epm config init`  
**Then** the CLI creates configuration directory  
**And** prompts for OCI Vault connection  
**And** creates template `applications.yaml`

##### SC-027: Version Check

**Given** installed CLI  
**When** I run `epm --version`  
**Then** the CLI shows version number  
**And** shows Python version  
**And** shows configuration location