# Proposal: EPM Audit CLI

## Problem Statement

Oracle's EPM Automate CLI covers day-to-day operations but has significant gaps for SOX audit and governance workflows:

1. **No artifact change tracking** — Cannot query what configuration changed, when, and by whom
2. **No EDM request history** — Cannot retrieve metadata deployment records
3. **No business rule inspection** — Cannot extract rule formulas for diff comparison
4. **No OCI infrastructure access** — Cannot monitor compute/storage/networking
5. **No governance checks** — Cannot query EDM policy violations

These gaps require manual workarounds (snapshot diffs, manual exports) that are:
- Time-consuming
- Error-prone
- Not audit-ready

## Why Now?

- SOX compliance requires automated audit trails
- Manual snapshot comparison doesn't scale
- Existing `extract-artifact-changes.py` shows the pattern but lacks CLI usability
- Credential manager (`credential_manager.py`) is ready for authentication

## Success Criteria

- [ ] CLI mirrors EPM Automate command style (`epm <verb> <noun>`)
- [ ] Authentication via existing credential manager (OAuth 2.0 + OCI Vault)
- [ ] All 4 critical gap commands implemented
- [ ] JSON output for scripting, table output for humans
- [ ] Works against real EPM Cloud instances (validated)
- [ ] Documentation with examples

## Out of Scope

- GUI/dashboard (CLI only)
- Real-time monitoring (polling-based)
- Automatic remediation (reporting only)
- ARCS/TRCS-specific commands (Phase 2)
- Windows PowerShell wrapper (Phase 2)

## Notes

- Build on existing `credential_manager.py` for auth
- Reuse patterns from `extract-artifact-changes.py` for API calls
- EPM Automate uses `epmautomate <verb> <noun>` — we use `epm <verb> <noun>`
- Focus on audit-relevant operations, not operational ones