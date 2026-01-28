# Quickstart: Container Image Integration Test Validation

**Feature**: Exact Object Count Validation  
**Last Updated**: 2026-01-22

## What Changed

Updated integration test validation from **minimum threshold checks** (≥5, ≥2, ≥1) to **exact count validation** (=5, =6, =1, =2, =3, =4, =2, =2) for 8 entity types.

## Quick Reference

### Expected Object Counts

| Entity | Count | Source |
|--------|-------|--------|
| Currency | 5 | Django initialization |
| SyncJob | 6 | 2 sync + 4 parse tasks |
| AAPUser | 1 | Admin user | <-- this is not Django admin user, it is user synced from AAP instance -->
| Organization | 2 | Test data |
| JobTemplate | 3 | Test data |
| Job | 4 | Test data |
| Project | 2 | Test data |
| Label | 2 | Test data |

### Validation Script Location

```
tests/integration/validate_results.py
```

### Run Integration Test

```bash
# Full test (CI or local)
./tests/integration/run_integration_test.sh --aap-version 2.6 --cleanup

# GitHub Actions (manual trigger)
# Actions → Container Integration Test → Run workflow
# Parameters: image_tag=main, aap_version=2.6

# Skip AAP setup (for faster iterations)
./tests/integration/run_integration_test.sh --skip-aap --cleanup
```

### Run Validation Only

```bash
# Inside task container
docker exec automation-dashboard-task pytest /app/tests/integration/validate_results.py -v

# From host (requires Django settings)
cd src/backend
pytest ../../tests/integration/validate_results.py -v
```

## Implementation Checklist

- [ ] Update `tests/integration/validate_results.py` to assert exact counts
- [ ] Change assertions from `assert count >= N` to `assert count == N`
- [ ] Add descriptive f-string messages: `f"Expected {expected} {Model.__name__} objects, got {actual}"`
- [ ] Validate all 8 entity types: Currency, SyncJob, AAPUser, Organization, JobTemplate, Job, Project, Label
- [ ] Test locally with `--skip-aap` mode for faster feedback
- [ ] Run full integration test to verify assertions pass
- [ ] Commit changes and push to branch `001-container-image-test`

## Common Issues

### Issue: Assertion Fails with "got 0"

**Cause**: SyncJob didn't complete successfully, no data synced

**Fix**: Check orchestration script polling phase. Verify SyncJob status = "completed" before validation runs.

### Issue: Assertion Fails with "got 10 Currency objects"

**Cause**: Database not cleaned up from previous test run

**Fix**: Run with `--cleanup` flag. Verify docker-compose down removes volumes.

### Issue: "ImportError: No module named pytest"

**Cause**: pytest not installed in container

**Fix**: Verify Dockerfile.backend includes pytest in requirements. Rebuild image.

### Issue: Assertion Fails with "got 3 Job objects" (expected 4)

**Cause**: setup_aap.py didn't create all test data, or sync failed for one job

**Fix**: Check AAP logs, verify setup_aap.py completed successfully. Check SyncJob error messages.

## Validation Example

```python
# tests/integration/validate_results.py (excerpt)

import pytest
from backend.apps.clusters.models import Job, Organization, JobTemplate
from backend.apps.common.models import Currency
from backend.apps.scheduler.models import SyncJob

@pytest.mark.django_db
def test_database_object_counts():
    """Validate exact object counts after data synchronization."""
    
    # Currency - standard set
    currency_count = Currency.objects.count()
    assert currency_count == 5, f"Expected 5 Currency objects, got {currency_count}"
    
    # SyncJob - sync operations
    syncjob_count = SyncJob.objects.count()
    assert syncjob_count == 6, f"Expected 6 SyncJob objects, got {syncjob_count}"
    
    # Organization - test data
    org_count = Organization.objects.count()
    assert org_count == 2, f"Expected 2 Organization objects, got {org_count}"
    
    # Job - test data
    job_count = Job.objects.count()
    assert job_count == 4, f"Expected 4 Job objects, got {job_count}"
    
    # ... (all 8 entities)
```

## Test Flow

```
1. Setup AAP (10-15 min)        → aap-dev creates AAP instance
2. Create Test Data (1-2 min)   → setup_aap.py creates objects
3. Start Containers (30 sec)    → docker-compose up
4. Configure Cluster (5 sec)    → setclusters command
5. Sync Data (30-60 sec)        → syncdata command
6. Wait for Completion (up to 5 min) → Poll SyncJob status
7. Validate Counts (< 1 sec)    → pytest validate_results.py ← THIS STEP
8. Cleanup (30 sec)             → docker-compose down
```

## Files Created/Modified

### Created (by this plan)
- `specs/001-container-image-test/plan.md` - Implementation plan
- `specs/001-container-image-test/research.md` - Research findings
- `specs/001-container-image-test/data-model.md` - Entity definitions
- `specs/001-container-image-test/contracts/validation-contract.md` - Validation contract
- `specs/001-container-image-test/quickstart.md` - This file

### To Be Modified (by `/speckit.tasks`)
- `tests/integration/validate_results.py` - Update assertions to exact counts

### Already Exists (no changes needed)
- `tests/integration/docker-compose.yml` - Container definitions
- `tests/integration/run_integration_test.sh` - Orchestration script
- `.github/workflows/integration-test.yml` - CI workflow
- `src/backend/tests/mock_aap/setup_aap.py` - Test data creation

## Next Steps

1. Run `/speckit.tasks` to generate detailed task breakdown
2. Implement `tests/integration/validate_results.py` with exact count assertions
3. Test locally: `./tests/integration/run_integration_test.sh --skip-aap --cleanup`
4. Verify in CI: Trigger GitHub Actions workflow manually
5. Document any issues or deviations from expected counts

## Documentation Links

- **Feature Spec**: [spec.md](spec.md)
- **Implementation Plan**: [plan.md](plan.md)
- **Data Model**: [data-model.md](data-model.md)
- **Validation Contract**: [contracts/validation-contract.md](contracts/validation-contract.md)
- **Research Findings**: [research.md](research.md)

## Contact

For questions about expected counts or validation failures, see:
- Reference test: `src/backend/tests/mock_aap/test_full.py`
- Test data source: `src/backend/tests/mock_aap/setup_aap.py`
