# Tasks: EPM Audit CLI

## Phase 1: Foundation

- [ ] 1.1 Create project structure (`epm_audit_cli/` directory)
- [ ] 1.2 Set up `pyproject.toml` with dependencies
- [ ] 1.3 Create `cli.py` entry point with Click group
- [ ] 1.4 Create `config/loader.py` to read `applications.yaml`
- [ ] 1.5 Create `clients/base.py` with `BaseAPIClient` class
- [ ] 1.6 Create `output/table.py` with Rich table formatter
- [ ] 1.7 Create `output/json_fmt.py` with JSON formatter
- [ ] 1.8 Create `output/csv_fmt.py` with CSV formatter

## Phase 2: Authentication

- [ ] 2.1 Integrate `credential_manager.py` into CLI
- [ ] 2.2 Implement `epm login <app>` command
- [ ] 2.3 Implement `epm logout` command
- [ ] 2.4 Add `--verify` flag to test connection
- [ ] 2.5 Implement token cache refresh logic
- [ ] 2.6 Add error handling for expired tokens

## Phase 3: Artifact Changes Command

- [ ] 3.1 Create `commands/artifact.py` module
- [ ] 3.2 Implement `epm artifact-changes` command
- [ ] 3.3 Create `clients/epm.py` with `EPMClient` class
- [ ] 3.4 Implement `get_artifact_modifications()` API call
- [ ] 3.5 Create `utils/classify.py` with material/operational logic
- [ ] 3.6 Add `--type` filter for artifact types
- [ ] 3.7 Add `--modified-by` filter
- [ ] 3.8 Add `--modified-by-exclude` filter
- [ ] 3.9 Implement pagination for large results
- [ ] 3.10 Add rate limiting handling with retries

## Phase 4: EDM Commands

- [ ] 4.1 Create `commands/edm.py` module
- [ ] 4.2 Create `clients/edm.py` with `EDMClient` class
- [ ] 4.3 Implement `epm edm-requests` command
- [ ] 4.4 Implement `epm edm-request --id <id>` command
- [ ] 4.5 Implement `epm edm-violations` command
- [ ] 4.6 Add `--status` filter (COMPLETED, PENDING, etc.)
- [ ] 4.7 Add `--from` / `--to` date filters

## Phase 5: Business Rule Commands

- [ ] 5.1 Create `commands/rules.py` module
- [ ] 5.2 Implement `epm rules --app <id>` command
- [ ] 5.3 Implement `epm rule --app <id> --id <rule-id>` command
- [ ] 5.4 Implement `epm rule-diff --app <id> --id <rule-id> --baseline <file>`
- [ ] 5.5 Add `--output file.txt` for rule export
- [ ] 5.6 Implement formula comparison logic
- [ ] 5.7 Handle large formulas with truncation warning

## Phase 6: OCI Commands (Optional)

- [ ] 6.1 Create `commands/oci.py` module
- [ ] 6.2 Create `clients/oci_client.py` with `OCIClient` class
- [ ] 6.3 Implement `epm oci-instances --compartment <id>` command
- [ ] 6.4 Implement `epm oci-storage --bucket <name>` command
- [ ] 6.5 Implement `epm oci-network --vcn <id>` command
- [ ] 6.6 Add tag filtering for EPM-related resources
- [ ] 6.7 Add `oci` as optional dependency in `pyproject.toml`

## Phase 7: IAM / IDCS Commands

- [x] 7.1 Create `commands/iam.py` module
- [x] 7.2 Create `clients/iam.py` with `IAMClient` class (wraps OCI IdentityClient)
- [x] 7.3 Implement `epm iam-users --compartment <id>` command
- [x] 7.4 Implement `epm iam-groups --compartment <id>` command
- [x] 7.5 Implement `epm iam-memberships --compartment <id>` command
- [x] 7.6 Implement `epm iam-access-review --compartment <id>` command (full SOX access review)
- [x] 7.7 Add `--filter service-accounts` to show only service accounts
- [x] 7.8 Add `--filter dormant` to show dormant accounts (no login >90 days)
- [x] 7.9 Add `--filter privileged` to show privileged users
- [x] 7.10 Add `--output csv` for SOX access review export format
- [x] 7.11 Implement dormant account detection (last login timestamp)
- [x] 7.12 Implement privileged user detection (admin group membership)
- [x] 7.13 Add SoD (Segregation of Duties) violation detection
- [x] 7.14 Add orphan account detection (no group memberships)

## Phase 7: Error Handling & UX

- [ ] 7.1 Create custom `EPMError` exception classes
- [ ] 7.2 Implement exit codes (401, 400, 503, 429)
- [ ] 7.3 Add suggestion text to all error messages
- [ ] 7.4 Implement `--dry-run` flag to show API calls
- [ ] 7.5 Add `--verbose` flag for debug logging
- [ ] 7.6 Implement progress indicators for long operations
- [ ] 7.7 Add confirmation prompts for production operations

## Phase 8: Installation & Documentation

- [ ] 8.1 Create `epm config init` command for setup
- [ ] 8.2 Create `epm --version` command
- [ ] 8.3 Write README.md with installation instructions
- [ ] 8.4 Write CLI reference documentation
- [ ] 8.5 Add example commands for common use cases
- [ ] 8.6 Create man page or help documentation
- [ ] 8.7 Test pip install in clean virtual environment

## Phase 9: Testing

- [ ] 9.1 Write unit tests for `utils/classify.py`
- [ ] 9.2 Write unit tests for output formatters
- [ ] 9.3 Write integration tests with mock API
- [ ] 9.4 Test against real EPM instance (with test credentials)
- [ ] 9.5 Test rate limiting and retry logic
- [ ] 9.6 Test authentication token refresh
- [ ] 9.7 Test error handling scenarios

## Verification

How to verify this change is complete:

- [ ] All commands from spec implemented and working
- [ ] Authentication works with existing credential manager
- [ ] Can query artifact changes from real FCCS instance
- [ ] Can retrieve EDM requests and violations
- [ ] Can extract and diff business rules
- [ ] OCI commands work (if implemented)
- [ ] IAM commands retrieve users, groups, memberships from IDCS/OCI IAM
- [ ] Access review generates SOX-compliant report with all sections
- [ ] Dormant and privileged user detection working
- [ ] CSV export format accepted by audit team
- [ ] Error messages are clear and actionable
- [ ] Documentation covers all commands
- [ ] `pip install` works in clean environment
- [ ] Unit tests pass with >80% coverage