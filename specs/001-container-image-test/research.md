# Research: Container Image Integration Test

**Feature**: Container Image Integration Test  
**Branch**: 001-container-image-test  
**Date**: 2026-01-22

## Research Overview

This document consolidates research findings for updating the integration test validation to use exact object counts instead of minimum thresholds.

## Research Question 1: Exact Object Counts from setup_aap.py

**Context**: Feature spec requires exact count validation (Currency=5, SyncJob=6, etc.) instead of minimum thresholds (≥5, ≥2, etc.). Need to confirm expected counts based on setup_aap.py script behavior.

**Decision**: Validate exact counts: Currency=5, SyncJob=6, AAPUser=1, Organization=2, JobTemplate=3, Job=4, Project=2, Label=2

**Rationale**:
- Analyzed `src/backend/tests/mock_aap/test_full.py` which tests against real AAP instance
- Test shows deterministic assertions after data sync completion:
  - `assert 5 == Currency.objects.count()` - 5 standard currencies created
  - `assert 6 == SyncJob.objects.count()` - 2 sync_jobs + 4 parse_job_data tasks
  - `assert 1 == AAPUser.objects.count()` - Single admin user
  - `assert 2 == Organization.objects.count()` - Test orgs
  - `assert 3 == JobTemplate.objects.count()` - Test templates
  - `assert 4 == Job.objects.count()` - Test jobs
  - `assert 2 == Project.objects.count()` - Test projects
  - `assert 2 == Label.objects.count()` - Test labels
- setup_aap.py creates fixed number of objects, not variable counts
- Exact count validation detects regressions (missing sync, duplicate objects, partial failures)

**Alternatives Considered**:
- **Minimum thresholds (≥)**: Rejected - too permissive, allows duplicate object bugs to pass
- **Range validation (5-7)**: Rejected - still allows bugs, unclear success criteria
- **Manual verification**: Rejected - error-prone, not automated

**Implementation Impact**: Update validate_results.py assertions from `assert count >= N` to `assert count == N` for all 8 entity types.

---

## Research Question 2: pytest Best Practices for Integration Test Assertions

**Context**: Need to determine best practices for pytest assertion messages and database connection in integration test context.

**Decision**: Use pytest with descriptive assertion messages and Django ORM database connection

**Rationale**:
- pytest provides clear assertion introspection without custom messages in simple cases
- For exact count validation, format: `assert Model.objects.count() == expected, f"Expected {expected} {Model.__name__} objects, got {Model.objects.count()}"`
- Django ORM already used in backend (constitution requirement), no new database library needed
- Django test database configuration provides isolation and cleanup
- Integration test connects to test database using Django settings

**Alternatives Considered**:
- **Direct SQL queries**: Rejected - bypasses Django ORM, doesn't match application code path
- **unittest assertions**: Rejected - pytest provides better failure output and fixture support
- **Custom validation framework**: Rejected - unnecessary complexity for straightforward count checks

**Implementation Impact**: validate_results.py uses Django ORM queries with pytest assertions and descriptive f-string messages.

---

## Research Question 3: Integration Test Database Connection Strategy

**Context**: validate_results.py needs to query PostgreSQL database after container startup. Need reliable connection strategy.

**Decision**: Use Django management command pattern with pytest-django

**Rationale**:
- Integration test already starts Django containers with database
- pytest-django provides `django_db` fixture for database access
- Django settings configured via environment variables in docker-compose
- Connection details: postgres:5432, database name from env, credentials from env
- validate_results.py can be run as: `docker exec task-container pytest /path/to/validate_results.py`
- Database polling (5 second intervals) already implemented in orchestration script for SyncJob completion

**Alternatives Considered**:
- **Standalone psycopg2 connection**: Rejected - requires credential management, doesn't match app architecture
- **REST API validation**: Rejected - tests API layer instead of database state, introduces extra failure points
- **Manual SQL inspection**: Rejected - not automated, error-prone

**Implementation Impact**: validate_results.py uses pytest-django with @pytest.mark.django_db decorator, runs inside task container.

---

## Research Question 4: Container Integration Test Orchestration Patterns

**Context**: Need to understand how orchestration script (run_integration_test.sh) manages test lifecycle and validation script invocation.

**Decision**: Bash script orchestrates phases: AAP setup → container startup → data sync → validation → cleanup

**Rationale**:
- Reviewed existing CI-INTEG-TEST.md documentation showing implemented pattern
- bash script provides good error handling (`set -e`), logging (phase markers), and cleanup (trap handlers)
- Phases:
  1. **Phase 1**: Clone aap-dev, setup AAP instance (10-15 minutes)
  2. **Phase 2**: Run setup_aap.py to create test data
  3. **Phase 3**: Build/pull container image, start docker-compose
  4. **Phase 4**: Run setclusters and syncdata management commands
  5. **Phase 5**: Poll database for SyncJob completion (5s intervals, 300s timeout)
  6. **Phase 6**: Run validate_results.py via docker exec
  7. **Phase 7**: Capture logs on failure, cleanup on success
- GitHub Actions workflow invokes bash script with parameters

**Alternatives Considered**:
- **Python orchestration**: Rejected - bash provides better system integration for Docker, subprocess management
- **Make-based workflow**: Rejected - less flexible for conditional execution, error handling
- **Docker Compose health checks only**: Rejected - can't validate business logic (object counts)

**Implementation Impact**: validate_results.py is invoked by run_integration_test.sh in Phase 6. Script receives pass/fail signal via pytest exit code.

---

## Technology Stack Summary

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Validation Framework | pytest + pytest-django | Constitution compliance, existing backend usage |
| Database Access | Django ORM | Constitution compliance, matches application pattern |
| Assertion Style | pytest assertions with f-strings | Clear failure messages, standard pytest pattern |
| Orchestration | Bash script | System integration, Docker management, error handling |
| CI Integration | GitHub Actions | Existing CI platform, manual trigger support |
| Container Runtime | Docker/Podman | Constitution requirement II, existing deployment pattern |

---

## Open Questions Resolution

All technical unknowns from Technical Context section resolved:
- ✅ Testing framework: pytest + pytest-django
- ✅ Database connection: Django ORM via pytest-django fixture
- ✅ Exact counts: Confirmed from test_full.py reference implementation
- ✅ Orchestration pattern: Bash script with phase markers
- ✅ Validation invocation: docker exec in Phase 6 of orchestration

**Ready for Phase 1**: All NEEDS CLARIFICATION items resolved. Proceeding to data model and contract generation.
