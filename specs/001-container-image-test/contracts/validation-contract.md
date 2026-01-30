# Integration Test Validation Contract

**Version**: 1.0.0  
**Feature**: Container Image Integration Test  
**Date**: 2026-01-22

## Contract Purpose

This contract defines the validation requirements for the container image integration test. The validation script (`validate_results.py`) MUST verify that data synchronization from AAP to the dashboard database produces exactly the expected number of objects.

## Validation Interface

### Input Requirements

**Prerequisites**:
1. AAP instance running and accessible (created by aap-dev)
2. Test data created in AAP via `setup_aap.py`
3. Dashboard containers running (postgres, redis, web, task)
4. `setclusters` command executed successfully
5. `syncdata` command executed successfully
6. SyncJob status = "completed" (verified by orchestration script)

**Environment**:
- Database: PostgreSQL 15+ accessible via Django ORM
- Python: 3.12+ with Django, pytest, pytest-django installed
- Execution Context: Inside task container or with Django settings configured

### Output Requirements

**Success Criteria**:
- Exit code: 0
- All 8 entity count assertions pass
- Clear test output showing passed assertions

**Failure Criteria**:
- Exit code: 1
- Clear assertion failure messages showing:
  - Expected count
  - Actual count
  - Entity name

## Validation Assertions

### Required Assertions (Exact Counts)

The validation script MUST assert these exact counts. Any deviation (more or fewer objects) MUST cause test failure.

```python
# Format: assert actual == expected, f"Expected {expected} {entity} objects, got {actual}"

# Currency - Standard currency set
assert Currency.objects.count() == 5, \
    f"Expected 5 Currency objects, got {Currency.objects.count()}"

# SyncJob - Sync operations + parse tasks
assert SyncJob.objects.count() == 6, \
    f"Expected 6 SyncJob objects, got {SyncJob.objects.count()}"

# AAPUser - Admin user
assert AAPUser.objects.count() == 1, \
    f"Expected 1 AAPUser object, got {AAPUser.objects.count()}"

# Organization - Test organizations
assert Organization.objects.count() == 2, \
    f"Expected 2 Organization objects, got {Organization.objects.count()}"

# JobTemplate - Test job templates
assert JobTemplate.objects.count() == 3, \
    f"Expected 3 JobTemplate objects, got {JobTemplate.objects.count()}"

# Job - Test jobs
assert Job.objects.count() == 4, \
    f"Expected 4 Job objects, got {Job.objects.count()}"

# Project - Test projects
assert Project.objects.count() == 2, \
    f"Expected 2 Project objects, got {Project.objects.count()}"

# Label - Test labels
assert Label.objects.count() == 2, \
    f"Expected 2 Label objects, got {Label.objects.count()}"
```

### Validation Breakdown

| Entity | Expected Count | Source | Rationale |
|--------|---------------|--------|-----------|
| Currency | 5 | Django initialization | Standard currency set (USD, EUR, GBP, JPY, CHF) |
| SyncJob | 6 | Scheduler | 2 sync_jobs + 4 parse_job_data tasks |
| AAPUser | 1 | AAP sync | Admin user from setup_aap.py |
| Organization | 2 | AAP sync | Test organizations from setup_aap.py |
| JobTemplate | 3 | AAP sync | Test job templates from setup_aap.py |
| Job | 4 | AAP sync | Test jobs from setup_aap.py |
| Project | 2 | AAP sync | Test projects from setup_aap.py |
| Label | 2 | AAP sync | Test labels from setup_aap.py |

## Contract Guarantees

### What This Test Validates

✅ **Data Synchronization Completeness**:
- All expected objects synced from AAP to dashboard database
- No missing objects (would fail with actual < expected)

✅ **Data Synchronization Correctness**:
- No duplicate objects created (would fail with actual > expected)
- Correct number of sync operations tracked

✅ **Database State Consistency**:
- Currency reference data properly initialized
- Foreign key relationships maintained (implicit via ORM)

### What This Test Does NOT Validate

❌ **Data Content**: Does not verify field values (names, descriptions, IDs)
❌ **Relationships**: Does not verify FK references or many-to-many links
❌ **Timestamps**: Does not verify created_at, updated_at, started, finished fields
❌ **Business Logic**: Does not verify cost calculations, filtering, or aggregations
❌ **API Endpoints**: Does not test REST API responses
❌ **UI Functionality**: Does not test frontend rendering

## Error Scenarios

### Scenario 1: Missing Objects (actual < expected)

**Example**: Only 3 Job objects created instead of 4

```
AssertionError: Expected 4 Job objects, got 3
```

**Possible Causes**:
- Partial sync failure (AAP API error for one job)
- Database transaction rollback
- setup_aap.py did not create all test data

**Required Action**: Test MUST fail, logs captured for debugging

---

### Scenario 2: Duplicate Objects (actual > expected)

**Example**: 10 Currency objects instead of 5

```
AssertionError: Expected 5 Currency objects, got 10
```

**Possible Causes**:
- Currency initialization ran twice (migration issue)
- Duplicate sync operation without proper deduplication
- Previous test data not cleaned up

**Required Action**: Test MUST fail, database inspection needed

---

### Scenario 3: SyncJob Failure

**Example**: SyncJob status = "failed" but test runs anyway

**Contract Requirement**: Orchestration script MUST check SyncJob status BEFORE running validation. Validation should never run if sync failed.

**If validation runs despite sync failure**: Likely 0 objects for synced entities, all assertions fail.

---

## Test Execution Contract

### Invocation

```bash
# Inside task container
pytest tests/integration/validate_results.py -v

# Via docker exec from orchestration script
docker exec automation-dashboard-task pytest /app/tests/integration/validate_results.py -v
```

### Expected Output (Success)

```
============================= test session starts ==============================
collected 1 item

tests/integration/validate_results.py::test_database_object_counts PASSED [100%]

============================== 1 passed in 0.50s ===============================
```

### Expected Output (Failure)

```
============================= test session starts ==============================
collected 1 item

tests/integration/validate_results.py::test_database_object_counts FAILED [100%]

=================================== FAILURES ===================================
___________________________ test_database_object_counts ________________________

    def test_database_object_counts():
>       assert Job.objects.count() == 4, f"Expected 4 Job objects, got {Job.objects.count()}"
E       AssertionError: Expected 4 Job objects, got 3
E       assert 3 == 4

tests/integration/validate_results.py:42: AssertionError
=========================== short test summary info ============================
FAILED tests/integration/validate_results.py::test_database_object_counts - A...
============================== 1 failed in 0.45s ================================
```

## Contract Versioning

### Version 1.0.0 (Current)

- Initial validation contract
- 8 entity types validated
- Exact count assertions (equality, not minimum thresholds)
- Based on setup_aap.py deterministic test data

### Future Considerations (Out of Scope)

- Field-level validation (e.g., verify specific organization names)
- Relationship validation (e.g., verify Job.organization_id references valid Organization)
- Performance metrics (e.g., sync duration, query performance)
- Multi-AAP version compatibility (different expected counts per version)

## Contract Compliance

**Implementation Requirements**:
1. ✅ validate_results.py MUST use pytest framework
2. ✅ validate_results.py MUST use Django ORM for database queries
3. ✅ validate_results.py MUST use exact equality assertions (==), not minimum (>=)
4. ✅ validate_results.py MUST provide descriptive assertion messages with expected vs actual
5. ✅ validate_results.py MUST be executable via `pytest` command
6. ✅ validate_results.py MUST exit with code 0 on success, 1 on failure

**Constitution Alignment**:
- ✅ Principle III (Comprehensive Testing): Provides integration test for AAP synchronization
- ✅ Principle IV (Automated Quality Gates): Provides clear pass/fail signal for CI
- ✅ Principle V (Documentation Standards): This contract documents validation requirements

## Reference Implementation

See `src/backend/tests/mock_aap/test_full.py` for reference test showing expected counts after full sync against real AAP instance. The integration test validation contract is derived from the assertions in that test.
