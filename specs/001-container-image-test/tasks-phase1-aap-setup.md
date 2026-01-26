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
- [ ] T006 Implement --aap-dev-version argument parsing (git commit SHA, branch name, or tag, default main)
- [ ] T007 Implement --skip-aap flag for reusing existing AAP instance
- [ ] T008 Implement structured logging functions (log_phase, log_info, log_error, log_success)
- [ ] T009 Implement prerequisites check function (validate docker/podman, git, curl availability)
- [ ] T010 Implement disk space check function for /tmp directory (minimum 10GB free)
- [ ] T011 Implement disk space check function for current directory (minimum 10GB free)
- [ ] T012 Implement TCP port check function (verify 44925/44926 availability based on version)
- [ ] T013 Implement aap-dev clone/update function (clone from https://github.com/ansible/aap-dev or update if exists)
- [ ] T014 Implement aap-dev version checkout (git checkout to specified commit/branch/tag if --aap-dev-version provided)
- [ ] T015 Implement AAP start function (execute aap-dev make aap with AAP_VERSION=2.6 or AAP_VERSION=2.5-next)
- [ ] T016 Implement AAP health check function (try /api/gateway/v1/ping/ first for 2.5+, fall back to /api/v2/ping/)
- [ ] T017 Implement health check polling (5-second interval, 600-second timeout, 120 attempts maximum)
- [ ] T018 Implement admin password retrieval using aap-dev make admin-password command
- [ ] T019 Implement AAP URL parsing and component extraction (protocol, address, port)
- [ ] T020 Implement aap_access.json generation with all fields (OAuth2 fields set to null, AAP fields populated)
- [ ] T021 Implement admin credentials validation (test login with retrieved password using curl)
- [ ] T022 Implement environment variable export (AAP_URL, AAP_PASSWORD, AAP_VERSION, AAP_USERNAME)
- [ ] T023 Implement skip-aap mode (validate existing AAP instance is running and reachable)
- [ ] T024 Implement comprehensive diagnostic capture on failure (container logs, disk space, port status, network checks)
- [ ] T025 Implement debugging guidance output (commands to inspect containers, aap-dev docs link, troubleshooting steps)
- [ ] T026 Add timing metrics to each phase (report duration for setup steps)
- [ ] T027 Make script executable (chmod +x setup_aap.sh)

**Checkpoint**: setup_aap.sh can start AAP and validate it's working

---

## Phase 3: AAP Cleanup Script Implementation

**Purpose**: Clean shutdown of AAP instances

- [ ] T028 Create tests/integration/cleanup_aap.sh with script skeleton
- [ ] T029 Implement --version argument parsing (optional, cleans all versions if not specified)
- [ ] T030 Implement --remove-aap-dev flag for removing aap-dev directory
- [ ] T031 Implement --force flag to skip confirmation prompts
- [ ] T032 Implement AAP shutdown function (cd aap-dev && make clean to remove kind cluster)
- [ ] T033 Implement aap-dev directory removal (if --remove-aap-dev specified)
- [ ] T034 Implement aap_access.json cleanup
- [ ] T035 Implement port verification (confirm ports 44925/44926 are freed)
- [ ] T036 Add cleanup confirmation prompt (list what will be cleaned, require --force or user confirmation)
- [ ] T037 Make script executable (chmod +x cleanup_aap.sh)

**Checkpoint**: cleanup_aap.sh can stop AAP and free resources

---

## Phase 4: Documentation

**Purpose**: Usage documentation and examples

- [ ] T038 [P] Document setup_aap.sh usage in README-phase1.md (all arguments including --aap-dev-version, examples, troubleshooting)
- [ ] T039 [P] Document cleanup_aap.sh usage in README-phase1.md (all flags including --force and --remove-aap-dev)
- [ ] T040 [P] Add prerequisites section to README-phase1.md (docker/podman, git, curl, 10GB disk space in /tmp and current dir)
- [ ] T041 [P] Add quick start section to README-phase1.md (TL;DR commands, common workflows)
- [ ] T042 [P] Add aap_access.json structure reference to README-phase1.md
- [ ] T043 [P] Add troubleshooting section to README-phase1.md (6 common issues: missing tools, disk space, port conflicts, timeout, password not found, debugging)
- [ ] T044 [P] Add example output to README-phase1.md (show expected [PHASE] markers and success indicators)

**Checkpoint**: Documentation complete, developers can follow README to setup AAP

---

## Phase 5: Testing & Validation

**Purpose**: Manual verification that scripts work correctly

- [ ] T045 Test setup_aap.sh with AAP 2.6 default (verify starts on port 44926, credentials work, health check passes, aap_access.json created)
- [ ] T046 Test setup_aap.sh with AAP 2.5 (verify starts on port 44925, credentials work, health check passes)
- [ ] T047 Test setup_aap.sh with --aap-dev-version flag (test with specific commit/tag, verify correct version checked out)
- [ ] T048 Test --skip-aap mode (start AAP once, run setup_aap.sh --skip-aap, verify reuses instance and validates it)
- [ ] T049 Test aap_access.json structure (verify all 10 fields present, OAuth2 fields are null, AAP fields populated correctly matching data-model)
- [ ] T050 Test environment variables (verify AAP_URL, AAP_PASSWORD, AAP_VERSION, AAP_USERNAME exported correctly)
- [ ] T051 Test cleanup_aap.sh without flags (verify stops AAP, frees ports 44925/44926, removes aap_access.json)
- [ ] T052 Test cleanup_aap.sh with --force (verify skips confirmation prompts)
- [ ] T053 Test cleanup_aap.sh with --remove-aap-dev and --clean-git (verify removes entire aap-dev directory)
- [ ] T054 Test error handling - missing prerequisites (verify clear error messages with installation commands)
- [ ] T055 Test error handling - insufficient disk space in /tmp (verify fails fast with diagnostic info)
- [ ] T056 Test error handling - insufficient disk space in current dir (verify fails fast with diagnostic info)
- [ ] T057 Test error handling - port conflicts (verify detects 44925/44926 in use, reports with lsof/netstat commands)
- [ ] T058 Test error handling - AAP startup timeout (verify comprehensive diagnostics: container logs, disk space, ports, network checks, debugging guidance)
- [ ] T059 Test error handling - health check failure (verify tries both endpoints, provides debugging commands)
- [ ] T060 Test on different machine/environment (verify portability across Linux systems with Docker/Podman)

**Checkpoint**: Phase 1 complete - AAP setup scripts work reliably

---

## Summary

**Total Tasks**: 60 tasks organized in 5 phases
- Phase 1 (Directory Setup): 3 tasks (T001-T003)
- Phase 2 (AAP Setup Script): 24 tasks (T004-T027)
- Phase 3 (Cleanup Script): 10 tasks (T028-T037) - **Note: T038 moved to Phase 4**
- Phase 4 (Documentation): 7 tasks (T038-T044)
- Phase 5 (Testing & Validation): 16 tasks (T045-T060)

**Parallel Opportunities**: 7 tasks marked with [P] in Phase 4 (documentation tasks can run in parallel after implementation complete)

**Key Deliverables**:
1. `tests/integration/setup_aap.sh` - Main setup script (~400-500 lines)
   - Prerequisites validation (Docker/Podman, Git, curl, disk space)
   - aap-dev repository management (clone/update, version checkout)
   - AAP lifecycle (start, health check with 2 endpoints, admin password retrieval)
   - Output artifacts (aap_access.json with 10 fields, 4 environment variables)
   - Comprehensive error handling and diagnostics
   
2. `tests/integration/cleanup_aap.sh` - Cleanup script (~150-200 lines)
   - AAP shutdown (make clean)
   - Container verification (confirm stopped/removed)
   - Optional git cleanup (remove aap-dev directory)
   - File cleanup (aap_access.json, environment variables)
   - Dry-run mode (--skip-cleanup)
   
3. `tests/integration/README-phase1.md` - Comprehensive documentation
   - Prerequisites (versions, disk requirements)
   - Quick start (TL;DR commands)
   - All script arguments and flags
   - aap_access.json structure reference
   - 6 troubleshooting scenarios (from quickstart-phase1.md)
   - Example outputs
   
4. `tests/integration/.gitignore` - Ignore patterns
   - aap-dev/ directory
   - aap_access.json
   - *.log files
   
5. `tests/integration/aap_access.json` - Generated runtime artifact (not checked into git)

**Estimated Effort**: 6-8 hours total
- Implementation: 4-5 hours (setup script 3 hours, cleanup script 1 hour, directory setup 15 minutes, .gitignore 15 minutes)
- Documentation: 1-2 hours (README-phase1.md)
- Testing & Validation: 1-2 hours (16 test scenarios)

**Dependencies**:
- Phase 1 must complete before Phase 2 (no data loading without AAP running)
- Phase 2 must complete before Phase 3 (cleanup script references setup implementation)
- Phase 3 must complete before Phase 4 (documentation describes both scripts)
- Phase 4 must complete before Phase 5 (testing follows documentation)

**Constitution Compliance**:
- ✅ Single Responsibility: Each script has one job (setup or cleanup)
- ✅ Explicit Over Implicit: All arguments and behaviors documented
- ✅ Fail Fast: Prerequisite validation before any AAP operations
- ✅ Self-Documenting: Structured logging with [PHASE] markers
- ✅ Minimal Dependencies: Only requires standard tools (bash, docker/podman, git, curl)

---

## Notes

- **Phase 1 scope**: AAP instance setup ONLY (from REFACTORING-SUMMARY.md). No test data, no containers, no data sync, no validation layers.
- **Phase 2-4**: Future phases documented in separate spec files (spec-phase2-aap-data.md, spec-phase3-containers.md, spec-phase4-validation.md)
- **Testing approach**: Manual verification sufficient for Phase 1. Automated tests (shellcheck, bats) may come in later phases.
- **Health check strategy**: From research-phase1.md - try /api/gateway/v1/ping/ first (AAP 2.5+), fall back to /api/v2/ping/ (AAP 2.4)
- **Password retrieval**: From research-phase1.md - use aap-dev make admin-password command (reads from Kubernetes secret)
- **Disk validation**: From clarifications - check both /tmp (aap-dev requirement) and current directory (script outputs), 10GB minimum for each
- **aap_access.json format**: From data-model-phase1.md - 10 fields (6 OAuth2 null, 4 AAP populated matching setup_aap.py output)

Phase 1 delivers foundation scripts that unblock all subsequent phases.
