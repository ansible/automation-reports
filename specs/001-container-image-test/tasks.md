# Tasks: Container Image Integration Test

**Input**: Design documents from `/specs/001-container-image-test/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: This feature IS the testing infrastructure. No separate test tasks needed - implementation creates the validation tests themselves.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Test Infrastructure Foundation)

**Purpose**: Create test infrastructure directory and base configuration files

- [ ] T001 Create tests/integration/ directory structure
- [ ] T002 Create tests/integration/.gitignore for temporary test files
- [ ] T003 [P] Create tests/integration/README.md with comprehensive test documentation
- [ ] T004 [P] Update root README.md with integration test section and link

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core test infrastructure that MUST be complete before user stories can be validated

**⚠️ CRITICAL**: No user story validation can work until this phase is complete

- [ ] T005 Create tests/integration/docker-compose.yml defining postgres, redis, web, task containers
- [ ] T006 [P] Create tests/integration/.env.example with environment variable template
- [ ] T007 Create tests/integration/run_integration_test.sh orchestration script (phases 1-7 structure)
- [ ] T008 Implement AAP setup phase in run_integration_test.sh (clone aap-dev, start AAP instance)
- [ ] T009 Implement test data creation phase in run_integration_test.sh (run setup_aap.py)
- [ ] T010 Implement container management phase in run_integration_test.sh (docker-compose up, health checks)
- [ ] T011 Implement sync phase in run_integration_test.sh (setclusters, syncdata commands)
- [ ] T012 Implement wait phase in run_integration_test.sh (poll SyncJob status, 5s interval, 300s timeout)
- [ ] T013 Implement cleanup phase in run_integration_test.sh (docker-compose down, AAP cleanup)
- [ ] T014 Add structured logging with [PHASE] markers and timing metrics to run_integration_test.sh
- [ ] T015 Add error handling and log capture on failure to run_integration_test.sh
- [ ] T016 Create .github/workflows/integration-test.yml for manual CI trigger

**Checkpoint**: Foundation ready - user story validation scripts can now be implemented

---

## Phase 3: User Story 4 - Database Object Validation with pytest (Priority: P1) 🎯 MVP

**Goal**: Automated pytest validation script that verifies exact database object counts after data synchronization

**Independent Test**: Run pytest validation script after manual sync and verify it detects correct/incorrect counts

**Why US4 First**: This is the PRIMARY update target. User Stories 1-3 infrastructure already exists (GitHub workflow, docker-compose, bash script). US4 validation script needs exact count updates.

### Implementation for User Story 4

- [ ] T017 [US4] Create tests/integration/validate_results.py pytest validation script skeleton
- [ ] T018 [US4] Import Django models in validate_results.py (Currency, SyncJob, AAPUser, Organization, JobTemplate, Job, Project, Label)
- [ ] T019 [US4] Implement test_database_object_counts() function with @pytest.mark.django_db decorator
- [ ] T020 [US4] Add Currency exact count assertion (assert Currency.objects.count() == 5) with descriptive message
- [ ] T021 [P] [US4] Add SyncJob exact count assertion (assert SyncJob.objects.count() == 6) with descriptive message
- [ ] T022 [P] [US4] Add AAPUser exact count assertion (assert AAPUser.objects.count() == 1) with descriptive message
- [ ] T023 [P] [US4] Add Organization exact count assertion (assert Organization.objects.count() == 2) with descriptive message
- [ ] T024 [P] [US4] Add JobTemplate exact count assertion (assert JobTemplate.objects.count() == 3) with descriptive message
- [ ] T025 [P] [US4] Add Job exact count assertion (assert Job.objects.count() == 4) with descriptive message
- [ ] T026 [P] [US4] Add Project exact count assertion (assert Project.objects.count() == 2) with descriptive message
- [ ] T027 [P] [US4] Add Label exact count assertion (assert Label.objects.count() == 2) with descriptive message
- [ ] T028 [US4] Integrate validate_results.py invocation into run_integration_test.sh Phase 6
- [ ] T029 [US4] Test validation script locally with existing test data (--skip-aap mode)
- [ ] T030 [US4] Update tests/integration/QUICKSTART.md with exact count table and validation commands

**Checkpoint**: US4 complete - pytest validation now checks exact counts instead of minimums

---

## Phase 4: User Story 1 - Manual CI Test Trigger for Container Images (Priority: P1)

**Goal**: Enable manual GitHub Actions workflow triggers to test specific container image versions

**Independent Test**: Trigger workflow via GitHub UI with test image tag, verify workflow completes and validation passes

### Implementation for User Story 1

- [ ] T031 [US1] Configure workflow_dispatch trigger in .github/workflows/integration-test.yml with inputs (image_tag, aap_version)
- [ ] T032 [US1] Add image pull step in workflow (supports quay.io registry authentication via GitHub secrets)
- [ ] T033 [US1] Add AAP setup job in workflow (runs aap-dev setup, exports AAP_URL and credentials)
- [ ] T034 [US1] Add container startup step in workflow (docker-compose up with image_tag variable substitution)
- [ ] T035 [US1] Add data sync step in workflow (setclusters + syncdata commands)
- [ ] T036 [US1] Add validation step in workflow (invoke pytest validate_results.py)
- [ ] T037 [US1] Add log capture step in workflow (on failure, collect container logs, AAP logs, database state)
- [ ] T038 [US1] Configure GitHub secrets for registry authentication (REGISTRY_QUAY_IO_USERNAME, REGISTRY_QUAY_IO_PASSWORD) - Manual: Repository Settings → Secrets and variables → Actions → New repository secret
- [ ] T039 [US1] Test workflow manually via GitHub UI with main branch image
- [ ] T040 [US1] Update specs/001-container-image-test/quickstart.md with GitHub Actions trigger instructions

**Checkpoint**: US1 complete - can trigger integration tests for any container image via GitHub UI

---

## Phase 5: User Story 2 - Local Development Testing (Priority: P2)

**Goal**: Enable developers to run integration tests locally with CLI flags for debugging and fast iteration

**Independent Test**: Run `./run_integration_test.sh --aap-version 2.6` locally and verify test passes

### Implementation for User Story 2

- [ ] T041 [P] [US2] Add --aap-version flag parsing to run_integration_test.sh
- [ ] T042 [P] [US2] Add --cleanup flag to run_integration_test.sh (cleanup after test completion)
- [ ] T043 [P] [US2] Add --skip-aap flag to run_integration_test.sh (reuse existing AAP instance)
- [ ] T044 [P] [US2] Add --image flag to run_integration_test.sh (specify custom container image)
- [ ] T045 [US2] Add --help flag and usage documentation to run_integration_test.sh
- [ ] T046 [US2] Implement conditional AAP cleanup based on --cleanup flag
- [ ] T047 [US2] Implement conditional AAP setup skip based on --skip-aap flag
- [ ] T048 [US2] Test script locally with --cleanup flag (verify resources removed)
- [ ] T049 [US2] Test script locally with --skip-aap flag (verify fast iteration)
- [ ] T050 [US2] Update tests/integration/README.md with local testing workflow and CLI flags

**Checkpoint**: US2 complete - developers can run tests locally with flexible options

---

## Phase 6: User Story 3 - Multi-AAP Version Testing (Priority: P2)

**Goal**: Support testing against both AAP 2.5 and 2.6 versions to ensure compatibility

**Independent Test**: Run tests with --aap-version 2.5 and --aap-version 2.6 separately, verify both pass

### Implementation for User Story 3

- [ ] T051 [US3] Add AAP version parameter to aap-dev setup in run_integration_test.sh
- [ ] T052 [US3] Configure port mapping for AAP 2.5 (44925) and 2.6 (44926) in run_integration_test.sh
- [ ] T053 [US3] Update docker-compose.yml to support AAP_URL environment variable (dynamic AAP address)
- [ ] T054 [US3] Add AAP version validation in run_integration_test.sh (accept only 2.5 or 2.6)
- [ ] T055 [US3] Test with AAP 2.5 locally (verify sync and validation pass)
- [ ] T056 [US3] Test with AAP 2.6 locally (verify sync and validation pass)
- [ ] T057 [US3] Add matrix strategy to .github/workflows/integration-test.yml (test both AAP versions in parallel)
- [ ] T058 [US3] Update specs/001-container-image-test/quickstart.md with multi-version testing examples

**Checkpoint**: US3 complete - integration tests work with both AAP 2.5 and 2.6

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and final improvements

- [ ] T059 [P] Create tests/integration/QUICKSTART.md quick reference guide for running tests (separate from specs/001-container-image-test/quickstart.md which is feature planning documentation)
- [ ] T060 [P] Update CI-INTEG-TEST.md with implementation details and workflow summary
- [ ] T061 [P] Add troubleshooting section to tests/integration/README.md (common issues, fixes)
- [ ] T062 Validate all 4 user stories work together (full integration test run)
- [ ] T063 Run integration test 3 times consecutively to verify reliability (SC-008 requirement)
- [ ] T064 Verify test completes within 20 minutes typical, 25 minutes maximum (SC-001, FR-018)
- [ ] T065 [P] Add inline comments to run_integration_test.sh for phase explanations
- [ ] T066 [P] Add inline comments to validate_results.py explaining expected counts source
- [ ] T067 Create .github/workflows/integration-test-schedule.yml for optional nightly runs (out of scope but recommended)
- [ ] T068 Final validation: Run specs/001-container-image-test/quickstart.md implementation checklist

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion - BLOCKS all user stories
- **User Story 4 (Phase 3)**: Depends on Foundational (Phase 2) - PRIMARY FOCUS
- **User Story 1 (Phase 4)**: Depends on Foundational (Phase 2) and US4 (Phase 3) - needs validation script
- **User Story 2 (Phase 5)**: Depends on Foundational (Phase 2) - can be parallel with US1
- **User Story 3 (Phase 6)**: Depends on Foundational (Phase 2) - can be parallel with US1/US2
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 2 (Foundational) MUST complete first
         ↓
    ┌────┴────┬────────┬────────┐
    ↓         ↓        ↓        ↓
  US4 (P1)  US1 (P1) US2 (P2) US3 (P2)
  Validation  CI      Local    Multi-AAP
    ↓
  US1 depends on US4 (needs validation script)
  US2, US3 independent (can parallelize)
```

### Within Each User Story

- **US4 (Validation)**:
  - T017-T019: Script skeleton (sequential)
  - T020-T027: Assertions (PARALLEL - different assertions, no dependencies)
  - T028-T030: Integration and docs (sequential, depends on assertions)

- **US1 (CI Trigger)**:
  - T031-T037: Workflow steps (sequential, ordered by execution flow)
  - T038-T040: Configuration and docs (can be parallel with workflow steps)

- **US2 (Local Testing)**:
  - T041-T044: Flag parsing (PARALLEL - independent flags)
  - T045-T047: Implementation (sequential)
  - T048-T050: Testing and docs (sequential)

- **US3 (Multi-AAP)**:
  - T051-T054: AAP version support (sequential)
  - T055-T056: Testing (PARALLEL - independent AAP versions)
  - T057-T058: CI and docs (sequential)

### Parallel Opportunities

**Phase 1 (Setup)**: T003-T004 can run in parallel (different documentation files)

**Phase 2 (Foundational)**: T006 can run in parallel with T005

**Phase 3 (US4 Validation)**: T021-T027 (all entity assertions) can run in parallel - each adds one assertion to the same function

**Phase 4 (US1 CI Trigger)**: T038 (GitHub secrets) can run in parallel with T031-T037 (workflow implementation)

**Phase 5 (US2 Local Testing)**: T041-T044 (flag parsing) can run in parallel

**Phase 6 (US3 Multi-AAP)**: T055-T056 (testing both versions) can run in parallel

**Phase 7 (Polish)**: T059-T061, T065-T066 (documentation tasks) can run in parallel

**Cross-Phase Parallelization**: Once Phase 2 completes, US2 (Phase 5) and US3 (Phase 6) can start in parallel with US1 (Phase 4), as long as US4 (Phase 3) completes first.

---

## Parallel Example: User Story 4 (Validation Script)

```bash
# After T020 completes, run T021-T027 in parallel (7 assertion additions)
# Each task adds one assertion statement to validate_results.py

# Terminal 1: Add SyncJob assertion
git checkout -b us4-syncjob-assertion
# Edit validate_results.py: add SyncJob assertion
git commit -m "Add SyncJob exact count assertion"

# Terminal 2: Add AAPUser assertion (parallel)
git checkout -b us4-aapuser-assertion
# Edit validate_results.py: add AAPUser assertion
git commit -m "Add AAPUser exact count assertion"

# ... (5 more terminals for remaining entities)

# After all assertions complete, merge to main branch
# Then proceed with T028 (integration into bash script)
```

---

## Task Estimates & MVP Scope

### Estimated Task Counts

- **Phase 1 (Setup)**: 4 tasks (~30 min)
- **Phase 2 (Foundational)**: 12 tasks (~6-8 hours) - Most time spent on bash script orchestration
- **Phase 3 (US4 Validation)**: 14 tasks (~2-3 hours) - PRIMARY FOCUS
- **Phase 4 (US1 CI Trigger)**: 10 tasks (~3-4 hours)
- **Phase 5 (US2 Local Testing)**: 10 tasks (~2-3 hours)
- **Phase 6 (US3 Multi-AAP)**: 8 tasks (~2-3 hours)
- **Phase 7 (Polish)**: 10 tasks (~2-3 hours)

**Total**: 68 tasks, estimated ~20-25 hours of implementation

### MVP Scope (Minimum Viable Product)

**MVP = Phase 1 + Phase 2 + Phase 3 (US4 only)**

This delivers:
- ✅ Test infrastructure (docker-compose, bash orchestration)
- ✅ Validation script with exact count assertions
- ✅ Local testing capability
- ✅ Basic documentation

**Not in MVP** (can be added incrementally):
- ❌ GitHub Actions CI trigger (US1)
- ❌ Advanced CLI flags (US2)
- ❌ Multi-AAP version support (US3)

### Incremental Delivery Strategy

1. **Sprint 1**: MVP (Phases 1-3) → Delivers core validation with exact counts
2. **Sprint 2**: Add US1 (Phase 4) → Enables CI testing
3. **Sprint 3**: Add US2+US3 (Phases 5-6) → Enhances developer experience
4. **Sprint 4**: Polish (Phase 7) → Documentation and reliability

---

## Implementation Strategy

### Recommended Approach

**Priority**: US4 (Phase 3) is the PRIMARY focus. Update validation script first.

**Rationale**: Based on plan.md summary, the test infrastructure (GitHub workflow, docker-compose, bash script) already exists. This feature focuses on updating the pytest validation from minimum thresholds (≥) to exact counts (=).

### Quick Win Path

1. Complete Phase 1 (Setup) - 30 minutes
2. Verify Phase 2 (Foundational) exists - if already implemented, skip to Phase 3
3. Implement Phase 3 (US4 Validation) - 2-3 hours
4. Test locally - 30 minutes
5. Update documentation - 1 hour

**Total Quick Win**: ~5 hours to update validation script with exact counts

### Full Implementation Path

1. Phases 1-3 (MVP) - ~10-12 hours
2. Add US1 (CI trigger) - ~4 hours
3. Add US2 (Local CLI) - ~3 hours
4. Add US3 (Multi-AAP) - ~3 hours
5. Polish - ~3 hours

**Total Full Implementation**: ~23-25 hours

---

## Success Criteria Verification

### How to Verify Each User Story

**US4 (Database Validation)**: 
```bash
# Run validation script after sync
docker exec automation-dashboard-task pytest /app/tests/integration/validate_results.py -v
# Verify all 8 entity assertions pass with exact counts
```

**US1 (CI Trigger)**:
```bash
# Trigger GitHub Actions workflow via UI
# Actions → Container Integration Test → Run workflow
# Inputs: image_tag=main, aap_version=2.6
# Verify workflow completes successfully
```

**US2 (Local Testing)**:
```bash
# Test with cleanup
./tests/integration/run_integration_test.sh --aap-version 2.6 --cleanup
# Test with skip-aap (fast iteration)
./tests/integration/run_integration_test.sh --skip-aap --cleanup
# Verify both complete successfully
```

**US3 (Multi-AAP)**:
```bash
# Test with AAP 2.5
./tests/integration/run_integration_test.sh --aap-version 2.5 --cleanup
# Test with AAP 2.6
./tests/integration/run_integration_test.sh --aap-version 2.6 --cleanup
# Verify both versions pass validation
```

### Success Criteria Mapping

- **SC-001**: Developers trigger test in GitHub Actions, receive results within 20 minutes → US1 (Phase 4)
- **SC-002**: Test validates images from quay.io and local builds → US1 + US2 (Phases 4-5)
- **SC-003**: Test catches AAP integration failures reliably → US4 (Phase 3)
- **SC-004**: Database validation detects incorrect counts with clear errors → US4 (Phase 3)
- **SC-005**: Test works with AAP 2.5 and 2.6 → US3 (Phase 6)
- **SC-006**: Developers run full integration test locally with single command → US2 (Phase 5)
- **SC-007**: Test provides clear failure diagnostics → Foundational (Phase 2) + US4 (Phase 3)
- **SC-008**: Test executes 10 times consecutively without failures → Verified in Phase 7 (T063)
- **SC-009**: Test completes on both x86_64 and aarch64 → Verified during testing
- **SC-010**: 95% of test runs complete without infrastructure failures → Monitor over time

---

## Notes for Implementation

### Critical Paths

1. **Database Connection**: validate_results.py must connect to test database via Django settings
2. **SyncJob Polling**: bash script MUST wait for SyncJob status='completed' before running validation
3. **Exact Counts**: All assertions MUST use `==` not `>=` to detect duplicate objects
4. **Error Messages**: All assertions MUST include descriptive f-strings showing expected vs actual

### Common Pitfalls

- ❌ Running validation before SyncJob completes (causes "got 0" errors)
- ❌ Not cleaning up database between test runs (causes "got 10" Currency objects)
- ❌ Using minimum threshold assertions (allows bugs to pass)
- ❌ Missing descriptive assertion messages (hard to debug failures)

### Reference Files

- **Expected Counts Source**: `src/backend/tests/mock_aap/test_full.py` (lines 75-94)
- **Test Data Creation**: `src/backend/tests/mock_aap/setup_aap.py`
- **Validation Contract**: `specs/001-container-image-test/contracts/validation-contract.md`
- **Data Model**: `specs/001-container-image-test/data-model.md`

---

**Task Breakdown Complete**: 68 tasks across 7 phases organized by user story

**Next Steps**: Start with MVP (Phases 1-3) focusing on US4 validation script update
