# Specification: CLI Core Fixes

## Requirements

### REQ-001: Consistent Method Naming

**As a** CLI user  
**I want** consistent snake_case method names  
**So that** commands work without AttributeError

#### Scenarios

##### SC-001: ConfigLoader method access

**Given** a ConfigLoader instance  
**When** I call `config.get_application("fccs_prod")`  
**Then** it returns the application configuration

**Edge Cases:**
- Application not found raises KeyError with helpful message
- Empty app_id raises ValueError

##### SC-002: snake_case aliases

**Given** ConfigLoader with camelCase methods  
**When** I need snake_case compatibility  
**Then** both `getApplication()` and `get_application()` work

---

### REQ-002: Valid Module Exports

**As a** CLI user  
**I want** all exported functions to exist  
**So that** imports don't fail

#### Scenarios

##### SC-001: commands/__init__.py exports

**Given** commands module  
**When** I import from `epm_audit_cli.commands`  
**Then** all exported functions exist and are callable

**Edge Cases:**
- Missing function raises AttributeError on import

---

### REQ-003: Token Persistence

**As a** CLI user  
**I want** my authentication to persist across commands  
**So that** I don't have to login before every command

#### Scenarios

##### SC-001: Token storage

**Given** successful authentication  
**When** the command completes  
**Then** the token is stored securely

##### SC-002: Token retrieval

**Given** a stored token  
**When** I run a new command  
**Then** the stored token is used automatically

##### SC-003: Token expiration

**Given** an expired token  
**When** I run a command  
**Then** I'm prompted to re-authenticate

**Edge Cases:**
- Token file permissions too open (warn)
- Corrupted token file (delete and prompt)
- Keyring not available (fallback to file)

---

### REQ-004: Self-Contained Authentication

**As a** CLI user  
**I want** authentication to work without external scripts  
**So that** I can install via pip

#### Scenarios

##### SC-001: Multiple auth backends

**Given** multiple auth backends available  
**When** I login  
**Then** the first available backend is used

Priority: keyring > file > env vars

##### SC-002: Config init

**Given** no config file  
**When** I run `epm config init`  
**Then** a template config is created

**Edge Cases:**
- Config file exists (prompt to overwrite)
- Permission denied (clear error message)

---

### REQ-005: Correct API Endpoints

**As a** CLI user  
**I want** API calls to use correct endpoints  
**So that** I get data instead of 404 errors

#### Scenarios

##### SC-001: Artifact changes endpoint

**Given** artifact-changes command  
**When** I query an application  
**Then** the correct EPM REST API endpoint is used

##### SC-002: Endpoint formatting

**Given** an endpoint with `{app}` placeholder  
**When** the request is made  
**Then** the placeholder is replaced with the app name

---

### REQ-006: Basic Test Coverage

**As a** developer  
**I want** basic tests for critical paths  
**So that** regressions are caught

#### Scenarios

##### SC-001: ConfigLoader tests

**Given** a valid config file  
**When** I run tests  
**Then** all ConfigLoader methods pass

##### SC-002: Command tests

**Given** mocked API responses  
**When** I run tests  
**Then** commands execute without error

---

### REQ-007: Config Init Command

**As a** new user  
**I want** a command to create config templates  
**So that** I can get started quickly

#### Scenarios

##### SC-001: Create config

**Given** no existing config  
**When** I run `epm config init`  
**Then** a template config is created at `config/applications.yaml`

##### SC-002: Interactive mode

**Given** `epm config init --interactive`  
**When** I answer prompts  
**Then** a customized config is created