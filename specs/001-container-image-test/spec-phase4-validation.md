# Feature Specification: Database Validation (Phase 4)

**Feature Branch**: `001-container-image-test`  
**Status**: Future - Not Yet Started  
**Phase**: Database Object Count Validation  
**Depends On**: Phase 1 (AAP Setup) ✅, Phase 2 (Test Data), Phase 3 (Sync)

## Overview

Phase 4 will focus on validating that data synchronization worked correctly by checking exact database object counts using pytest.

## Scope (Future)

**Will Include**:
- pytest validation script (`validate_results.py`)
- Exact count assertions for all entity types
- Clear error messages showing expected vs actual counts
- Integration with test orchestration script

**Entities to Validate**:
- Currency (expected: 5)
- SyncJob (expected: 6)
- AAPUser (expected: 1)
- Organization (expected: 2)
- JobTemplate (expected: 3)
- Job (expected: 4)
- Project (expected: 2)
- Label (expected: 2)

## Prerequisites

- Phase 1 complete: AAP instance running
- Phase 2 complete: AAP has test data
- Phase 3 complete: Data synced to dashboard database
- pytest and pytest-django installed
- Database accessible from validation script

## Success Criteria

- pytest script validates all entity counts correctly
- Script fails with clear messages if counts don't match
- Script can be run independently for debugging
- Integration with main test orchestration script
- Fast execution (< 30 seconds)

## To Be Detailed

This spec will be fully developed when Phase 3 is complete. It will include:
- Detailed user stories
- pytest test case design
- Django ORM query patterns
- Assertion message templates
- CI integration approach
- Implementation plan
- Task breakdown

## Notes

This was part of the original `spec.md` focus. Now deferred to Phase 4 after foundational phases are complete.

See original `spec.md` and `tasks.md` for detailed validation requirements.
