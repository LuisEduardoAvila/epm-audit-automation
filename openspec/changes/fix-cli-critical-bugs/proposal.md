# Proposal: Fix CLI Critical Bugs

## Problem Statement

The EPM Audit CLI has 8 critical bugs that make it non-functional:
1. Method name mismatch (`get_application()` vs `getApplication()`) - causes AttributeError
2. `iam_group` exported but doesn't exist - ImportError
3. `list_applications()` doesn't exist - AttributeError
4. Credential manager import fails for pip install - broken auth
5. No token persistence - must login before every command
6. Wrong API endpoints - 404 errors
7. Missing Data Exchange command - README claims it exists
8. Zero test coverage

These bugs block all production use. The CLI cannot work in its current state.

## Success Criteria

- [ ] All method names use consistent snake_case
- [ ] All exports in `__init__.py` exist
- [ ] Token persistence works across commands
- [ ] Auth works without external credential manager
- [ ] API endpoints match EPM REST API
- [ ] Basic tests pass
- [ ] `epm config init` command creates template config

## Out of Scope

- Data Exchange command (separate change)
- Forms-specific command (separate change)
- SoD configurable rules (enhancement)
- Dormant user detection implementation (enhancement)

## Notes

This is a blocking fix - CLI cannot be used until these are resolved.
Split into multiple Pi tasks to allow parallel execution where possible.