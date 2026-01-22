# Implementation Plan: Container Image Integration Test

**Branch**: `001-container-image-test` | **Date**: 2026-01-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-container-image-test/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Update existing integration test infrastructure to validate exact database object counts (Currency=5, SyncJob=6, AAPUser=1, Organization=2, JobTemplate=3, Job=4, Project=2, Label=2) instead of minimum thresholds. The test infrastructure (GitHub Actions workflow, docker-compose, bash orchestration script) is already implemented. This plan focuses on updating the pytest validation script to assert exact counts based on setup_aap.py behavior.

## Technical Context

**Language/Version**: Python 3.12+, Bash (orchestration scripts)  
**Primary Dependencies**: pytest (validation), Docker/Podman (container runtime), aap-dev (AAP instance), Django ORM (database queries)  
**Storage**: PostgreSQL 15 (test database), test data created by setup_aap.py script  
**Testing**: pytest for validation assertions, bash scripts for orchestration, GitHub Actions for CI  
**Target Platform**: Linux (Ubuntu 22.04+ in CI, developer machines with Docker/Podman)  
**Project Type**: Testing infrastructure (integration tests)  
**Performance Goals**: Test completion < 20 minutes (typical), < 25 minutes (maximum)  
**Constraints**: Must validate exact object counts, fail with clear assertion messages on mismatch  
**Scale/Scope**: Single feature update affecting 1 validation script, 8 entity types, ~10 assertion statements

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Security-First Development (Constitution I)
- **Status**: PASS
- **Rationale**: Integration test uses existing OAuth2 authentication to AAP via setup_aap.py. No new security requirements introduced. Validation script only reads database state; no credential handling.

### ✅ Containerized Deployment (Constitution II)
- **Status**: PASS  
- **Rationale**: Test infrastructure already uses Docker containers (postgres, redis, web, task). This update modifies only validation logic, not deployment architecture.

### ✅ Comprehensive Testing (Constitution III)
- **Status**: PASS
- **Rationale**: This feature IS the testing infrastructure. Updates enhance test accuracy by validating exact counts instead of minimums. Aligns with constitution requirement for "integration tests for AAP synchronization workflows."

### ✅ Automated Quality Gates (Constitution IV)
- **Status**: PASS
- **Rationale**: Integration test runs in GitHub Actions CI workflow. Updated validation script will provide clearer pass/fail signals for merge decisions.

### ✅ Documentation Standards (Constitution V)
- **Status**: PASS
- **Rationale**: Feature includes comprehensive documentation (spec.md with clarifications, this plan.md, existing README.md in test infrastructure). Will update quickstart.md with exact count expectations.

**Constitution Compliance**: ALL GATES PASS - No violations, no exceptions needed.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Existing project structure - test infrastructure already exists
src/backend/
├── tests/
│   └── mock_aap/
│       ├── setup_aap.py         # Creates test data (2 orgs, 3 templates, 4 jobs, etc.)
│       ├── test_full.py         # Reference test showing expected counts
│       └── fixtures/            # AAP API response fixtures
└── manage.py

tests/                            # DOES NOT EXIST YET - will be created
└── integration/                  # To be created by this feature
    ├── docker-compose.yml        # Defines postgres, redis, web, task containers
    ├── run_integration_test.sh   # Orchestration script with AAP setup
    ├── validate_results.py       # pytest script - PRIMARY UPDATE TARGET
    ├── README.md                 # Comprehensive documentation
    └── QUICKSTART.md             # Quick reference guide

.github/workflows/
└── integration-test.yml          # Manual CI trigger workflow

specs/001-container-image-test/
├── spec.md                       # Feature specification (completed)
├── plan.md                       # This file
├── research.md                   # Phase 0 output (to be generated)
├── data-model.md                 # Phase 1 output (to be generated)
├── quickstart.md                 # Phase 1 output (to be generated)
└── contracts/                    # Phase 1 output (validation contract)
```

**Structure Decision**: Existing integration test structure in `/tests/integration/` (to be created). Backend tests remain in `src/backend/tests/`. This feature creates new integration test directory separate from backend unit tests, following constitution principle III for test organization.

## Complexity Tracking

**No Violations**: Constitution Check passed all gates. No complexity justification needed.

---

## Phase 0 Output: Research (✅ COMPLETED)

**File**: [research.md](research.md)

**Key Findings**:
1. Exact object counts confirmed from `test_full.py` reference implementation
2. pytest + pytest-django chosen for validation framework (constitution compliance)
3. Django ORM for database access (matches application pattern)
4. Bash orchestration script invokes validation via docker exec

**All NEEDS CLARIFICATION items resolved** - Ready for Phase 1.

---

## Phase 1 Output: Design & Contracts (✅ COMPLETED)

### Data Model
**File**: [data-model.md](data-model.md)

Defines 8 validated entities with expected counts, relationships, and validation rules:
- Currency (5), SyncJob (6), AAPUser (1)
- Organization (2), JobTemplate (3), Job (4)
- Project (2), Label (2)

### Validation Contract
**File**: [contracts/validation-contract.md](contracts/validation-contract.md)

Specifies validation requirements:
- Exact equality assertions (==, not >=)
- Descriptive error messages with expected vs actual
- pytest execution contract with exit codes
- Success/failure output examples

### Quickstart Guide
**File**: [quickstart.md](quickstart.md)

Quick reference for:
- Expected object counts table
- Run commands (full test, validation only)
- Common issues and fixes
- Implementation checklist

### Agent Context Update
**Status**: ✅ Updated `.github/agents/copilot-instructions.md`

Added to context:
- Language: Python 3.12+, Bash
- Frameworks: pytest, Docker, Django ORM
- Database: PostgreSQL 15
- Project type: Testing infrastructure

---

## Phase 1 Re-Check: Constitution Compliance (✅ PASS)

All constitution principles remain satisfied after design phase:
- ✅ Security: No credential handling in validation
- ✅ Containers: Test infrastructure uses Docker
- ✅ Testing: Enhanced integration test accuracy
- ✅ Quality Gates: Clear pass/fail in CI
- ✅ Documentation: Comprehensive artifacts generated

**No design changes required** - Constitution compliance maintained.

---

## Next Steps

**This command stops here** - Phase 1 complete. `/speckit.plan` does not create `tasks.md`.

**To proceed with implementation**:
```bash
/speckit.tasks
```

This will generate detailed task breakdown for implementing the validation script updates.

---

## Summary of Generated Artifacts

| Artifact | Path | Purpose |
|----------|------|---------|
| Implementation Plan | [plan.md](plan.md) | This file - overall plan and context |
| Research Findings | [research.md](research.md) | Technology decisions and rationale |
| Data Model | [data-model.md](data-model.md) | Entity definitions and expected counts |
| Validation Contract | [contracts/validation-contract.md](contracts/validation-contract.md) | Validation requirements and guarantees |
| Quickstart Guide | [quickstart.md](quickstart.md) | Quick reference and commands |
| Agent Context | `.github/agents/copilot-instructions.md` | Updated AI agent context |

**Branch**: `001-container-image-test`  
**Feature Spec**: [spec.md](spec.md)  
**Implementation Plan**: [plan.md](plan.md)

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
