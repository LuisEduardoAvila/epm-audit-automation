# Oracle REST API Documentation Review - Summary

*Validated API patterns from official Oracle EPM REST API documentation*

**Source:** [Oracle Fusion Cloud EPM REST APIs](https://docs.oracle.com/en/cloud/saas/enterprise-performance-management-common/prest/index.html)  
**Document Version:** G42939-02 (November 2025)  
**Extracted:** February 26, 2026

---

## Key Architectural Validations

### ✅ URL Structure Patterns CONFIRMED

| Application | Base URL Pattern | Status |
|-------------|------------------|--------|
| **Common EPM APIs** | `/interop/rest/{version}/` | ✅ Confirmed |
| **Planning (PBCS)** | `/HyperionPlanning/rest/v{version}/` | ✅ Confirmed |
| **Financial Consolidation (FCCS)** | `/interop/rest/{version}/` | ✅ Confirmed |
| **Security APIs** | `/interop/rest/security/{version}/` | ✅ Confirmed |
| **Migration** | `/interop/rest/{version}/` | ✅ Confirmed |
| **Data Management** | `/interop/rest/{version}/` | ✅ Confirmed |

### ✅ Authentication Methods CONFIRMED

| Method | Status | Notes |
|--------|--------|-------|
| **Basic Authentication** | ✅ Supported | Username@domain + Password |
| **OAuth 2.0** | ✅ Supported | Recommended for automation |
| **Device Flow** | ✅ Documented | For OAuth without browser |
| **Token-based** | ✅ Available | Session management |

### ✅ REST API Versions CONFIRMED

- **v1** - Base APIs (widely supported)
- **v2** - Enhanced APIs (snapshots, config)
- **v3** - Latest (Planning-specific)

**Version Discovery Endpoint:**
```
GET /interop/rest/v1/services/
```

---

## FCCS API Endpoints CONFIRMED

### Journals APIs

| Operation | Method | Endpoint Pattern |
|-----------|--------|------------------|
| Retrieve Journals | GET | `/applications/{app}/journals` |
| Retrieve Journal Details | GET | `/applications/{app}/journals/{id}` |
| Import Journals | POST | `/applications/{app}/journals/import` |
| Export Journals | POST | `/applications/{app}/journals/export` |
| Perform Journal Actions | POST | `/applications/{app}/journals/actions` |
| Period Update | POST | `/applications/{app}/period/update` |

### Consolidation Rulesets

| Operation | Method | Endpoint Pattern |
|-----------|--------|------------------|
| Export Rulesets | POST | `/applications/{app}/consolidation/rulesets/export` |
| Import Rulesets | POST | `/applications/{app}/consolidation/rulesets/import` |

### Supplemental Data

| Operation | Method | Endpoint Pattern |
|-----------|--------|------------------|
| Import Supplemental Data | POST | `/applications/{app}/supplementaldata/import` |
| Export Supplemental Data | POST | `/applications/{app}/supplementaldata/export` |

### Task Manager

| Operation | Method | Endpoint Pattern |
|-----------|--------|------------------|
| Deploy Templates | POST | `/taskmanager/templates/deploy` |
| Update Task Status | PUT | `/taskmanager/tasks/{id}/status` |

### Enterprise Journals

| Operation | Method | Endpoint Pattern |
|-----------|--------|------------------|
| Monitor Journals | GET | `/enterprisejournals/monitor` |
| Retrieve Journals | GET | `/enterprisejournals` |
| Update Posting Status | PUT | `/enterprisejournals/{id}/postingstatus` |
| Update Validation Status | PUT | `/enterprisejournals/{id}/validationstatus` |

---

## Planning (PBCS) API Endpoints CONFIRMED

### Core Operations

| Resource | Method | Endpoint Pattern |
|----------|--------|------------------|
| Get Job Definitions | GET | `/HyperionPlanning/rest/v3/applications/{app}/jobs` |
| Execute Job | POST | `/HyperionPlanning/rest/v3/applications/{app}/jobs` |
| Get Rules | GET | `/HyperionPlanning/rest/v3/applications/{app}/rules` |
| Execute Rule | POST | `/HyperionPlanning/rest/v3/applications/{app}/rules/{id}/execute` |
| Get Rulesets | GET | `/HyperionPlanning/rest/v3/applications/{app}/rulesets` |
| Import Data | POST | `/HyperionPlanning/rest/v3/applications/{app}/data/import` |
| Export Data | POST | `/HyperionPlanning/rest/v3/applications/{app}/data/export` |
| Import Metadata | POST | `/HyperionPlanning/rest/v3/applications/{app}/metadata/import` |
| Export Metadata | POST | `/HyperionPlanning/rest/v3/applications/{app}/metadata/export` |
| Clear Cube | POST | `/HyperionPlanning/rest/v3/applications/{app}/clearcube` |
| Refresh Cube | POST | `/HyperionPlanning/rest/v3/applications/{app}/refreshcube` |
| Compact Cube | POST | `/HyperionPlanning/rest/v3/applications/{app}/compactcube` |
| Import Security | POST | `/HyperionPlanning/rest/v3/applications/{app}/security/import` |
| Export Security | POST | `/HyperionPlanning/rest/v3/applications/{app}/security/export` |
| Export Audit | GET | `/HyperionPlanning/rest/v3/applications/{app}/audit` |

### Forms & Grids

| Resource | Method | Endpoint Pattern |
|----------|--------|------------------|
| Get Forms | GET | `/HyperionPlanning/rest/v3/applications/{app}/forms` |
| Get Form Data | GET | `/HyperionPlanning/rest/v3/applications/{app}/forms/{id}/data` |
| Update Form Data | PUT | `/HyperionPlanning/rest/v3/applications/{app}/forms/{id}/data` |

### Plan Type Maps

| Resource | Method | Endpoint Pattern |
|----------|--------|------------------|
| Get Plan Type Maps | GET | `/HyperionPlanning/rest/v3/applications/{app}/plantypemaps` |

---

## Security API Endpoints CONFIRMED

### Users

| Operation | Method | Endpoint Pattern |
|-----------|--------|------------------|
| List Users | GET | `/interop/rest/security/{version}/users` |
| Create User | POST | `/interop/rest/security/{version}/users` |
| Get User | GET | `/interop/rest/security/{version}/users/{id}` |
| Update User | PUT | `/interop/rest/security/{version}/users/{id}` |
| Delete User | DELETE | `/interop/rest/security/{version}/users/{id}` |

### Groups

| Operation | Method | Endpoint Pattern |
|-----------|--------|------------------|
| List Groups | GET | `/interop/rest/security/{version}/groups` |
| Create Group | POST | `/interop/rest/security/{version}/groups` |
| Get Group | GET | `/interop/rest/security/{version}/groups/{id}` |
| Update Group | PUT | `/interop/rest/security/{version}/groups/{id}` |
| Delete Group | DELETE | `/interop/rest/security/{version}/groups/{id}` |
| Add User to Group | POST | `/interop/rest/security/{version}/groups/{id}/users` |
| Remove User from Group | DELETE | `/interop/rest/security/{version}/groups/{id}/users/{userId}` |

### Roles & Access

| Operation | Method | Endpoint Pattern |
|-----------|--------|------------------|
| Import Security | POST | `/interop/rest/security/{version}/security/import` |
| Export Security | POST | `/interop/rest/security/{version}/security/export` |

---

## Migration & Maintenance APIs CONFIRMED

### Snapshots

| Operation | Method | Endpoint Pattern |
|-----------|--------|------------------|
| Create Snapshot | POST | `/interop/rest/v2/snapshots` |
| Get Snapshots | GET | `/interop/rest/v2/snapshots` |
| Delete Snapshot | DELETE | `/interop/rest/v2/snapshots/{id}` |
| Copy from Instance | POST | `/interop/rest/v2/snapshots/copyfrominstance` |
| Copy to SFTP | POST | `/interop/rest/v2/config/services/copytosftp` |

### Service Management

| Operation | Method | Endpoint Pattern |
|-----------|--------|------------------|
| Refresh Application | POST | `/interop/rest/v2/applications/{app}/refresh` |
| Clone Instance | POST | `/interop/rest/v2/applications/clone` |
| Backup | POST | `/interop/rest/v2/applications/backup` |
| Daily Maintenance | GET/PUT | `/interop/rest/v2/config/dailymaintenance` |
| Usage Simulation | GET | `/interop/rest/v2/usagesimulation` |

---

## Data Management APIs CONFIRMED

| Operation | Method | Endpoint Pattern |
|-----------|--------|------------------|
| Execute DMS Script | POST | `/interop/rest/{version}/jobs/executedms` |
| Get Data Load Details | GET | `/interop/rest/{version}/dataloads/{id}` |

---

## EDM (Enterprise Data Management) Considerations

From the documentation review, EDM has its own REST API structure separate from the common EPM APIs. Key patterns:

- **Requests API:** `/edm/rest/v1/requests`
- **Views API:** `/edm/rest/v1/views`
- **Nodes API:** `/edm/rest/v1/nodes`

**Note:** EDM APIs require separate authentication and have their own versioning scheme. Our approach of using EDM as the source for metadata changes is architecturally sound based on Oracle's documentation.

---

## Key Implementation Notes from Oracle Docs

### ⚠️ Important Limitations

1. **Version Compatibility**
   - Not all APIs available in all versions
   - Check `/interop/rest/v1/services/` for available endpoints
   - V2 APIs require specific version support

2. **Asynchronous Operations**
   - Import/Export jobs run asynchronously
   - Use job ID to poll for status
   - Typical: `GET /jobs/{id} until status = SUCCESS`

3. **Authentication Best Practices**
   - OAuth 2.0 recommended for automation
   - Basic Auth acceptable for scripts
   - Tokens expire and require refresh

4. **Rate Limiting**
   - Documented but limits not specified
   - Implement exponential backoff
   - Monitor for HTTP 429 (Too Many Requests)

5. **Error Handling**
   - Standard HTTP status codes
   - Error details in response body
   - Job failures indicated in job status

---

## Confirmed Artifact Modification Approach

Oracle's documentation confirms **no native "artifact modification" API exists** that returns only configuration changes. Instead, changes must be tracked via:

1. **Job Logs** - Track import/export/execution
2. **Security Audit** - Track user/permission changes
3. **Application-Specific** - APIs vary by product

**Our filtering approach is validated as necessary:**
- Track artifact exports and compare baselines
- Monitor job execution for modifications
- Filter operational noise at the application level

---

## Files in Repository

| File | Contents |
|------|----------|
| `oracle_epm_rest_api.pdf` | Full official documentation (5.1MB) |
| `oracle_rest_api_full_text.txt` | Text extraction for searching |
| `oracle_api_toc.txt` | Table of contents |
| `fccs_api_endpoints.txt` | FCCS-specific section |

---

## Next Steps: Implementing Extraction Scripts

Based on documentation review, our extraction scripts should:

1. **Use correct base URLs:**
   - FCCS: `/interop/rest/v1/`
   - PBCS: `/HyperionPlanning/rest/v3/`
   - Security: `/interop/rest/security/v1/`

2. **Handle OAuth 2.0 flow:**
   - Device flow for server-side
   - Token refresh before expiry

3. **Poll for async operations:**
   - Import/Export jobs return job ID
   - Poll until complete

4. **Filter appropriately:**
   - Job execution logs (noise)
   - Actual artifact changes (material)

5. **Test against your instance:**
   - Available APIs vary by version/patch
   - Validate endpoint availability

---

*Last Updated: February 26, 2026*  
*Oracle Documentation: G42939-02 (Nov 2025)*  
*Status: Architecture validated, ready for implementation*
