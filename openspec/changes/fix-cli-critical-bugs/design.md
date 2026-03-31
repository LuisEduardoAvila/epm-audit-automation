# Design: CLI Critical Bug Fixes

## Overview

Fix 8 critical bugs that make the CLI non-functional. Approach: minimal changes, preserve existing API where possible, add backward compatibility aliases.

## Architecture Changes

### 1. Method Naming (ConfigLoader)

**Current:** camelCase (`getApplication()`, `getApplications()`)
**Fix:** Add snake_case aliases, keep camelCase for backward compatibility

```python
# config/loader.py
class ConfigLoader:
    # Existing camelCase methods
    def getApplication(self, app_id: str) -> Dict[str, Any]: ...
    def getApplications(self) -> Dict[str, Dict[str, Any]]: ...
    
    # New snake_case aliases
    def get_application(self, app_id: str) -> Dict[str, Any]:
        return self.getApplication(app_id)
    
    def get_applications(self) -> Dict[str, Dict[str, Any]]:
        return self.getApplications()
    
    def list_applications(self) -> List[Dict[str, Any]]:
        """Return list of app info dicts (matches commands usage)"""
        return [
            {"id": app_id, **app_config}
            for app_id, app_config in self.getApplications().items()
        ]
```

### 2. Missing Exports

**Current:** `iam_group` exported but doesn't exist
**Fix:** Remove from `__init__.py` exports (function is `iam_group` command group, not separate export)

```python
# commands/__init__.py
__all__ = [
    # ... existing ...
    "iam_users", "iam_groups", "iam_memberships", "iam_access_review",
    # Remove "iam_group" - it's the command group decorator, not an export
]
```

### 3. Token Persistence

**Location:** New `epm_audit_cli/auth/` module

```
epm_audit_cli/auth/
├── __init__.py
├── backend.py      # AuthBackend ABC
├── keyring_backend.py  # Keyring auth
├── file_backend.py     # File-based auth
├── env_backend.py      # Environment variable auth
└── manager.py      # TokenManager
```

**TokenManager interface:**
```python
class TokenManager:
    def __init__(self, backend: str = "auto"):
        self.backend = self._select_backend(backend)
    
    def get_token(self, app_id: str) -> Optional[str]:
        """Get cached token for app"""
    
    def store_token(self, app_id: str, token: str) -> None:
        """Store token for app"""
    
    def clear_token(self, app_id: str) -> None:
        """Clear stored token"""
    
    def is_valid(self, app_id: str) -> bool:
        """Check if token is valid (not expired)"""
```

**Token storage locations:**
- keyring: `epm-audit-cli://{app_id}`
- file: `~/.epm/tokens/{app_id}.token`
- env: `EPM_TOKEN_{APP_ID}`

### 4. Self-Contained Auth

**Remove:** External `credential_manager` import
**Add:** Built-in auth with multiple backends

```python
# commands/login.py
def login(ctx, app, verify, backend):
    # Priority: keyring > file > env
    token_manager = TokenManager(backend=backend)
    
    if token_manager.is_valid(app):
        token = token_manager.get_token(app)
    else:
        # Interactive auth
        token = _authenticate_interactive(app_config)
        token_manager.store_token(app, token)
```

### 5. API Endpoints

**Current issues:**
- Wrong endpoint paths
- Unformatted `{app}` placeholders

**Fix in `clients/base.py`:**
```python
class BaseAPIClient:
    def _format_endpoint(self, endpoint: str, app: str) -> str:
        """Replace placeholders in endpoint"""
        return endpoint.format(app=app)
    
    # Use EPM REST API v3 for Planning/PBCS/FCCS
    EPM_ENDPOINTS = {
        "artifact_changes": "/HyperionPlanning/rest/v3/applications/{app}/jobs/artifactModificationReport",
        "rules": "/HyperionPlanning/rest/v3/applications/{app}/rules",
        "edm_requests": "/interop/rest/v1/edm/requests",
    }
```

### 6. Test Structure

```
tests/
├── __init__.py
├── conftest.py      # Fixtures
├── test_config.py   # ConfigLoader tests
├── test_auth.py     # Auth backend tests
├── test_clients/    # API client tests
│   ├── test_base.py
│   └── test_iam.py
├── test_commands/   # Command tests
│   ├── test_login.py
│   ├── test_artifact.py
│   └── test_iam.py
└── fixtures/
    └── sample_config.yaml
```

### 7. Config Init Command

```python
# commands/config.py
@click.group(name="config")
def config_group():
    """Configuration commands"""
    pass

@config_group.command(name="init")
@click.option("--force", is_flag=True, help="Overwrite existing config")
@click.option("--interactive", is_flag=True, help="Interactive mode")
@click.pass_context
def config_init(ctx, force, interactive):
    """Initialize configuration file"""
    config_path = Path("config/applications.yaml")
    
    if config_path.exists() and not force:
        raise click.ClickException("Config exists. Use --force to overwrite.")
    
    if interactive:
        config = _interactive_config()
    else:
        config = _template_config()
    
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.dump(config, default_flow_style=False))
    
    console.print(f"[green]✓[/green] Created {config_path}")
```

## Implementation Order

1. **Phase 1: Method naming** - Add snake_case aliases (no breaking changes)
2. **Phase 2: Fix exports** - Remove non-existent exports
3. **Phase 3: Token persistence** - New auth module
4. **Phase 4: Config init** - New command
5. **Phase 5: API endpoints** - Fix endpoint paths
6. **Phase 6: Tests** - Add basic test coverage

## Open Questions

- Should we support OCI Vault for token storage? (Add as optional backend)
- Should we validate tokens against the API on startup? (Performance vs security)