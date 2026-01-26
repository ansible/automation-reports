# Tasks: AAP Instance Setup (Phase 1)

**Input**: [spec-phase1-aap-setup.md](spec-phase1-aap-setup.md), [plan-phase1-aap-setup.md](plan-phase1-aap-setup.md)  
**Prerequisites**: Spec ✅, Plan ✅  
**Focus**: AAP instance setup using aap-dev ONLY

**Tests**: Manual verification - run scripts and verify AAP starts correctly

## Format: `[ID] [P?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- All tasks are for Phase 1 - AAP setup only

---

## Phase 1: Directory Setup

**Purpose**: Create test infrastructure directory

- [ ] T001 Create tests/integration/ directory
- [ ] T002 Create tests/integration/.gitignore (ignore aap-dev/ and *.log files)
- [ ] T003 [P] Create tests/integration/README-phase1.md with AAP setup documentation

---

## Phase 2: AAP Setup Script Implementation

**Purpose**: Core AAP setup functionality

- [ ] T004 Create tests/integration/setup_aap.sh with script skeleton and argument parsing
- [ ] T005 Implement --aap-version argument parsing (2.5 or 2.6, default 2.6)
- [ ] T006 Implement --skip-aap flag for reusing existing AAP instance
- [ ] T007 Implement structured logging functions (log_phase, log_info, log_error, log_success)
- [ ] T008 Implement prerequisites check function (validate docker/podman, git, curl availability)
- [ ] T009 Implement disk space check function (require minimum 10GB free space)
- [ ] T010 Implement port check function (verify 44925/44926 availability based on version)
- [ ] T011 Implement aap-dev clone/update function (clone from https://github.com/ansible/aap-dev or update if exists)
- [ ] T012 Implement AAP start function (execute aap-dev commands for version 2.5 or 2.6)
- [ ] T013 Implement AAP health check function (poll /api/v2/ping/ with 30-second interval, 600-second timeout)
- [ ] T014 Implement admin password retrieval from aap-dev output (parse logs or config files)
- [ ] T015 Implement admin credentials validation (test login with retrieved password)
- [ ] T016 Implement environment variable export (AAP_URL, AAP_PASSWORD, AAP_VERSION)
- [ ] T017 Implement skip-aap mode (validate existing AAP instance is running and reachable)
- [ ] T018 Add error handling and cleanup on failure (capture logs, provide diagnostic info)
- [ ] T019 Add timing metrics to each phase (report duration for setup steps)
- [ ] T020 Make script executable (chmod +x setup_aap.sh)

**Checkpoint**: setup_aap.sh can start AAP and validate it's working

---

## Phase 3: AAP Cleanup Script Implementation

**Purpose**: Clean shutdown of AAP instances

- [ ] T021 Create tests/integration/cleanup_aap.sh with script skeleton
- [ ] T022 Implement --version argument parsing (optional, cleans all versions if not specified)
- [ ] T023 Implement AAP shutdown function (stop containers via aap-dev commands)
- [ ] T024 Implement aap-dev directory cleanup (optional --remove-aap-dev flag)
- [ ] T025 Implement port verification (confirm ports 44925/44926 are freed)
- [ ] T026 Add cleanup confirmation (list what will be cleaned, require --force or confirmation)
- [ ] T027 Make script executable (chmod +x cleanup_aap.sh)

**Checkpoint**: cleanup_aap.sh can stop AAP and free resources

---

## Phase 4: Documentation

**Purpose**: Usage documentation and examples

- [ ] T028 [P] Document setup_aap.sh usage in README-phase1.md (arguments, examples, troubleshooting)
- [ ] T029 [P] Document cleanup_aap.sh usage in README-phase1.md
- [ ] T030 [P] Add prerequisites section to README-phase1.md (docker, git, curl, disk space)
- [ ] T031 [P] Add quick start section to README-phase1.md (common commands)
- [ ] T032 [P] Add troubleshooting section to README-phase1.md (port conflicts, timeout issues)
- [ ] T033 [P] Add example output to README-phase1.md (show expected log messages)

**Checkpoint**: Documentation complete, developers can follow README to setup AAP

---

## Phase 5: Testing & Validation

**Purpose**: Manual verification that scripts work correctly

- [ ] T034 Test setup_aap.sh with AAP 2.6 (verify starts on port 44926, credentials work, health check passes)
- [ ] T035 Test setup_aap.sh with AAP 2.5 (verify starts on port 44925, credentials work, health check passes)
- [ ] T036 Test --skip-aap mode (start AAP once, run setup_aap.sh --skip-aap, verify reuses instance)
- [ ] T037 Test cleanup_aap.sh (stop AAP, verify ports freed, verify resources cleaned)
- [ ] T038 Test error handling (missing prerequisites, disk space issues, port conflicts)
- [ ] T039 Test on different machine/environment (verify portability)
- [ ] T040 Document test results and any issues found

**Checkpoint**: Phase 1 complete - AAP setup scripts work reliably

---

## Notes

- **Phase 1 scope**: AAP instance setup ONLY. No test data, no containers, no sync, no validation.
- **Phase 2+**: Will be documented in separate spec/plan/tasks files
- **Testing approach**: Manual verification sufficient for Phase 1. Automated tests come in later phases.
- **Estimated effort**: 4-6 hours total for implementation and testing

## Summary

Phase 1 delivers:
- ✅ setup_aap.sh - Start AAP 2.5 or 2.6
- ✅ cleanup_aap.sh - Stop AAP and free resources
- ✅ README-phase1.md - Usage documentation
- ✅ Manual testing verification

This unblocks development of Phase 2 (test data creation) and beyond.
