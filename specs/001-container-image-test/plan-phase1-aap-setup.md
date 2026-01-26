# Implementation Plan: AAP Instance Setup (Phase 1)

**Branch**: `001-container-image-test` | **Date**: 2026-01-26 | **Spec**: [spec-phase1-aap-setup.md](spec-phase1-aap-setup.md)

## Summary

Create bash script to automatically setup AAP instance (2.5 or 2.6) using aap-dev repository. Script will handle cloning, starting AAP, retrieving credentials, health checking, and cleanup. This is Phase 1 of the integration test infrastructure - focus on AAP setup only.

## Technical Context

**Language/Version**: Bash 4.0+  
**Primary Dependencies**: Docker/Podman, Git, curl, aap-dev repository  
**Testing**: Manual verification - run script, verify AAP starts and responds  
**Target Platform**: Linux (developer machines with Docker/Podman)  
**Performance Goals**: AAP startup < 10 minutes (typical)  
**Constraints**: Must support both AAP 2.5 and 2.6, must handle cleanup gracefully  
**Scale/Scope**: Single bash script (~300-400 lines), no database interactions yet

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Security-First Development (Constitution I)
- **Status**: PASS
- **Rationale**: Uses aap-dev's existing OAuth2 authentication. No new credential storage needed. Admin password retrieved from aap-dev output and stored only in environment variables.

### ✅ Containerized Deployment (Constitution II)
- **Status**: PASS  
- **Rationale**: AAP runs in containers via aap-dev (Docker-based). Script manages container lifecycle.

### ✅ Comprehensive Testing (Constitution III)
- **Status**: PASS
- **Rationale**: This IS testing infrastructure (Phase 1). Health check validates AAP is working. Later phases will add full integration tests.

### ✅ Automated Quality Gates (Constitution IV)
- **Status**: PASS
- **Rationale**: Health check acts as quality gate. Script fails fast if AAP doesn't start correctly.

### ✅ Documentation Standards (Constitution V)
- **Status**: PASS
- **Rationale**: Comprehensive spec and plan documents. Will include README with usage examples.

**Constitution Compliance**: ALL GATES PASS

## Project Structure

### Documentation (this feature)

```text
specs/001-container-image-test/
├── spec-phase1-aap-setup.md       # Phase 1 spec (AAP setup only)
├── plan-phase1-aap-setup.md       # This file
├── tasks-phase1-aap-setup.md      # Task breakdown for Phase 1
├── spec-phase2-aap-data.md        # Future: AAP test data creation
├── spec-phase3-containers.md      # Future: Container setup & sync
├── spec-phase4-validation.md      # Future: Database validation
└── spec.md                        # Original full spec (reference)
```

### Source Code

```text
tests/                              # To be created
└── integration/                    # Phase 1 creates this
    ├── setup_aap.sh                # Main AAP setup script - PRIMARY TARGET
    ├── cleanup_aap.sh              # AAP cleanup script
    ├── README.md                   # Phase 1 documentation
    └── .gitignore                  # Ignore aap-dev clone directory

# Phase 2+ (future):
# tests/integration/setup_aap_data.sh
# tests/integration/docker-compose.yml
# tests/integration/validate_results.py
```

**Structure Decision**: Keep Phase 1 focused on AAP setup only. Separate scripts for setup and cleanup. Later phases will add data population, containers, and validation.

## Complexity Tracking

**No Violations**: Phase 1 is intentionally simple - just AAP setup, no complex orchestration yet.

---

## Phase 0 Output: Research (✅ COMPLETED)

**File**: [research-phase1.md](research-phase1.md)

**Key Findings**:
1. aap-dev provides standardized make targets for AAP lifecycle management
2. Admin password accessible via ~/.aap-dev/admin_password.txt
3. Health check endpoints well-defined (/api/gateway/v1/ping/ for 2.5+, /api/v2/ping/ for 2.4)
4. aap_access.json can be generated with bash string manipulation
5. Disk space checks straightforward with df command
6. Bash is appropriate for Phase 1 orchestration

**All Technical Unknowns Resolved** - Ready for Phase 1.

---

## Phase 1 Output: Design & Contracts (✅ COMPLETED)

### Data Model
**File**: [data-model-phase1.md](data-model-phase1.md)

Defines Phase 1 data artifacts:
- aap_access.json structure with all fields and validation rules
- Environment variables (AAP_URL, AAP_PASSWORD, AAP_VERSION, AAP_USERNAME)
- aap-dev configuration and lifecycle
- AAP instance health states and monitoring
- Data flow from setup through export

### Script Contracts
**File**: [contracts-phase1/setup-script-contract.md](contracts-phase1/setup-script-contract.md)

Specifies interface guarantees:
- Command-line interface with options and exit codes
- Standard output format with phase markers
- Error output with diagnostics and debugging guidance
- Output artifacts (aap_access.json, environment variables)
- Prerequisites validation contract
- Health check polling strategy
- Cleanup script interface

### Quickstart Guide
**File**: [quickstart-phase1.md](quickstart-phase1.md)

Quick reference for:
- TL;DR commands
- Prerequisites checklist
- Expected behavior and timeline
- Troubleshooting common issues
- Configuration reference
- Common workflows
- FAQ

---

## Phase 1 Re-Check: Constitution Compliance (✅ PASS)

All constitution principles remain satisfied after design phase:
- ✅ Security: Admin password handled securely (environment variables, not logged)
- ✅ Containers: AAP runs in containers via aap-dev
- ✅ Testing: Health check validates setup, manual verification documented
- ✅ Quality Gates: Script fails fast with clear errors
- ✅ Documentation: Comprehensive quickstart and contract docs

**No design changes required** - Constitution compliance maintained.

---

## Next Steps

**This command stops here** - Phase 1 design complete. Ready for implementation.

**To proceed with implementation**:
Review [tasks-phase1-aap-setup.md](tasks-phase1-aap-setup.md) for detailed task breakdown.

---

## Summary of Generated Artifacts

| Artifact | Path | Purpose |
|----------|------|---------|
| Implementation Plan | [plan-phase1-aap-setup.md](plan-phase1-aap-setup.md) | This file - overall plan and context |
| Research Findings | [research-phase1.md](research-phase1.md) | Technology decisions and rationale |
| Data Model | [data-model-phase1.md](data-model-phase1.md) | Entity definitions and data flow |
| Script Contract | [contracts-phase1/setup-script-contract.md](contracts-phase1/setup-script-contract.md) | Interface guarantees and error handling |
| Quickstart Guide | [quickstart-phase1.md](quickstart-phase1.md) | Quick reference and troubleshooting |
| Tasks Breakdown | [tasks-phase1-aap-setup.md](tasks-phase1-aap-setup.md) | Implementation tasks (already exists) |

**Branch**: `001-container-image-test`  
**Feature Spec**: [spec-phase1-aap-setup.md](spec-phase1-aap-setup.md)  
**Implementation Plan**: [plan-phase1-aap-setup.md](plan-phase1-aap-setup.md)

**Estimated Effort**: 4-6 hours (scripting + testing + documentation)

**File**: `tests/integration/setup_aap.sh`

**Core Functions**:
1. Parse command-line arguments (--aap-version, --skip-aap, --cleanup)
2. Validate prerequisites (docker/podman, git, curl, disk space)
3. Clone/update aap-dev repository
4. Start AAP instance on correct port
5. Wait for AAP to be ready (health check with timeout)
6. Retrieve and validate admin credentials
7. Export AAP_URL and AAP_PASSWORD for later use
8. Structured logging with [PHASE] markers

**File**: `tests/integration/cleanup_aap.sh`

**Core Functions**:
1. Stop AAP instance (all versions or specific version)
2. Remove aap-dev working directory
3. Free ports and resources

### Phase 2: AAP Test Data (Future Spec)

Will create `setup_aap_data.sh` to populate AAP with test organizations, projects, templates, jobs, users.

### Phase 3: Container Setup (Future Spec)

Will create `docker-compose.yml` and orchestration for postgres, redis, web, task containers.

### Phase 4: Validation (Future Spec)

Will create `validate_results.py` pytest script for database object count validation.

---

## Success Criteria

### Phase 1 Complete When:

- [ ] `setup_aap.sh` successfully starts AAP 2.5 on port 44925
- [ ] `setup_aap.sh` successfully starts AAP 2.6 on port 44926
- [ ] Admin credentials are retrieved and validated
- [ ] Health check confirms AAP API is responding
- [ ] `--skip-aap` mode reuses existing instance
- [ ] `cleanup_aap.sh` stops AAP and frees resources
- [ ] README.md documents usage with examples
- [ ] Script fails gracefully with clear errors when prerequisites missing

---

## Next Steps

**After this plan**:
1. Create `tasks-phase1-aap-setup.md` with detailed task breakdown
2. Implement `setup_aap.sh` script
3. Implement `cleanup_aap.sh` script
4. Test on developer machine
5. Document usage in README.md

**Future phases** (separate specs):
- Phase 2: AAP test data creation
- Phase 3: Container orchestration and sync
- Phase 4: Database validation with pytest

---

## Summary

Phase 1 is intentionally minimal: **just get AAP running and validated**. This unblocks development and testing while keeping scope manageable. Later phases will build on this foundation.

**Key Deliverables**:
- `setup_aap.sh` - AAP instance setup script
- `cleanup_aap.sh` - AAP cleanup script
- `README.md` - Usage documentation
- Tests: Manual verification that AAP starts and responds

**Estimated Effort**: 4-6 hours (scripting + testing + documentation)
