# Tasks: Fix CLI Critical Bugs

## Phase 1: Method Naming (No Breaking Changes)

- [x] 1.1 Add `get_application()` alias to ConfigLoader (calls `getApplication()`)
- [x] 1.2 Add `get_applications()` alias to ConfigLoader (calls `getApplications()`)
- [x] 1.3 Add `list_applications()` method to ConfigLoader (returns list of app info dicts)
- [x] 1.4 Update commands to use snake_case methods (optional, backward compatible)

## Phase 2: Fix Exports

- [x] 2.1 Remove `iam_group` from `commands/__init__.py` exports (it's a decorator, not a function)
- [x] 2.2 Verify all exports in `__init__.py` exist in their modules
- [x] 2.3 Run `python -c "from epm_audit_cli.commands import *"` to verify no ImportError

## Phase 3: Token Persistence

- [x] 3.1 Create `epm_audit_cli/auth/__init__.py`
- [x] 3.2 Create `epm_audit_cli/auth/backend.py` with AuthBackend ABC
- [x] 3.3 Create `epm_audit_cli/auth/keyring_backend.py` (keyring storage)
- [x] 3.4 Create `epm_audit_cli/auth/file_backend.py` (file storage in `~/.epm/`)
- [x] 3.5 Create `epm_audit_cli/auth/env_backend.py` (environment variable fallback)
- [x] 3.6 Create `epm_audit_cli/auth/manager.py` with TokenManager class
- [ ] 3.7 Update `commands/login.py` to use TokenManager instead of credential_manager
- [ ] 3.8 Update `cli.py` CLIContext to check for stored tokens on startup
- [ ] 3.9 Add `--token-backend` option to login command

## Phase 4: Config Init Command

- [x] 4.1 Create `epm_audit_cli/commands/config.py` with config_group command
- [x] 4.2 Implement `config init` with template config generation
- [x] 4.3 Add `--interactive` mode for guided config creation
- [x] 4.4 Register config_group in `cli.py` main group
- [x] 4.5 Create template YAML in `epm_audit_cli/templates/config_template.yaml`

## Phase 5: API Endpoints

- [ ] 5.1 Add EPM_ENDPOINTS constant to `clients/base.py` with correct paths
- [ ] 5.2 Add `_format_endpoint()` method to BaseAPIClient
- [ ] 5.3 Update `commands/artifact.py` to use correct endpoint
- [ ] 5.4 Verify EDM and Rules endpoints are correct
- [ ] 5.5 Add integration test for endpoint URLs

## Phase 6: Tests

- [ ] 6.1 Create `tests/__init__.py`
- [ ] 6.2 Create `tests/conftest.py` with fixtures (sample config, mock API)
- [ ] 6.3 Create `tests/test_config.py` for ConfigLoader tests
- [ ] 6.4 Create `tests/test_auth.py` for auth backend tests
- [ ] 6.5 Create `tests/test_clients/test_base.py` for BaseAPIClient tests
- [ ] 6.6 Create `tests/fixtures/sample_config.yaml`
- [ ] 6.7 Add pytest to dev dependencies in `pyproject.toml`
- [ ] 6.8 Run `pytest` and verify all tests pass

## Phase 7: Integration

- [ ] 7.1 Update README with new auth workflow
- [ ] 7.2 Add `epm config init` to getting started guide
- [ ] 7.3 Update CHANGELOG with bug fixes
- [ ] 7.4 Create git tag for fixed version

## Verification

How to verify this change is complete:

- [ ] All Phase 1-6 tasks complete
- [ ] `python -c "from epm_audit_cli import *"` works
- [ ] `epm config init` creates valid config template
- [ ] `epm login fccs_prod` stores token (check `~/.epm/tokens/`)
- [ ] `epm artifact-changes fccs_prod` works after login
- [ ] `pytest tests/` passes
- [ ] No imports from external credential_manager