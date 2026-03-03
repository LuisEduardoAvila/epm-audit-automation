# Skill Pattern Documentation

This document explains how the EPM Audit Automation project could be packaged as an OpenClaw skill, and why we chose to keep it as a project for now.

## Overview

The EPM Audit project contains specialized domain knowledge (Oracle EPM Cloud APIs, SOX compliance, artifact types) that makes it a strong candidate for skill conversion. However, it's currently maintained as a regular project while we document the skill pattern.

## OpenSpec Documentation

Full skill specifications are documented in OpenSpec format:

```
openspec/changes/epmaudit-skill-wrapper/
├── proposal.md     # Why/what of the skill pattern
├── design.md       # Architecture and implementation details  
├── specs/          # Requirements and scenarios
└── tasks.md        # Implementation checklist
```

## Two Conversion Options

### Option A: Full Conversion (Future)
- Move all scripts to `skills/epm-audit/scripts/`
- Move docs to `skills/epm-audit/references/`
- Single source of truth in skills/
- **Best for:** Stable, mature systems

### Option B: Thin Wrapper (Documented, Not Implemented)
- Keep project in `projects/epm-audit-automation/`
- Add thin `skills/epm-audit/` with SKILL.md
- Skill provides natural language triggers
- **Best for:** Active development phase

**Current Decision:** Document Option B but don't implement it. The project stays as-is until it stabilizes.

## When to Convert

Consider converting to a skill when:
- The audit scripts are stable and feature-complete
- You're not making frequent changes to extraction logic
- You want natural language access ("Audit FCCS")
- Other team members need easy access without knowing file paths

Keep as a project when:
- Still developing and testing new artifact types
- Experimenting with different audit approaches
- Need flexibility to restructure frequently
- Want full visibility into all code during development

## Skill-Worthiness Assessment

### ✅ Yes — Domain Expertise
- Oracle EPM Cloud APIs (25+ endpoints)
- SOX compliance and materiality rules
- 40+ artifact types across 6 applications
- SOX-critical classification logic

### ✅ Yes — Specialized Workflows  
- Multi-step extraction sequences
- Cross-app dependency tracking (EDM → FCCS → PBCS)
- Materiality filtering for compliance
- Before/after comparison patterns

### ✅ Yes — Complexity
- 13,501 bytes of specialized documentation
- Configuration management for multiple apps
- Authentication and credential handling
- Output formatting and reporting

### ⚠️ Not Yet — Stability
- Still in active development
- Scripts may change frequently
- Output formats being refined
- New artifact types being added

## How the Skill Would Work (Option B)

**Natural Language Triggers:**
- *"Audit FCCS"* → Triggers skill → Runs `extract-fccs-audit.py`
- *"Check PBCS changes"* → Runs artifact extraction
- *"SOX materiality filter"* → Analyzes for compliance

**Progressive Disclosure:**
1. **Metadata** (always available): Name, description triggers
2. **SKILL.md** (on trigger): Quick reference, 500 lines max
3. **References** (on demand): Detailed docs from project

**Configuration:**
```yaml
# ~/.openclaw/config/epm_config.md
---
applications:
  FCCS:
    url: https://epm-cloud.oracle.com/pod/FCCS
    # ... credentials
---
```

## Next Steps

1. **Continue development** in `projects/epm-audit-automation/`
2. **Reference specs** in `openspec/changes/epmaudit-skill-wrapper/` when ready
3. **Decide to implement** Option B when convenient
4. **Migrate to Option A** once fully stable

## See Also

- OpenSpec change: `openspec/changes/epmaudit-skill-wrapper/`
- Skill creation guide: `~/.npm-global/lib/node_modules/openclaw/skills/skill-creator/SKILL.md`
- Main project: `README.md` (this folder)
