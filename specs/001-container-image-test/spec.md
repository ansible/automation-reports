# Feature Specification: Container Image Integration Test

**Feature Branch**: `001-container-image-test`  
**Created**: 2026-01-22  
**Status**: Draft  
**Input**: User description: "Add comprehensive integration test for container image with manual CI trigger. Test locally built or registry images against real AAP instance using aap-dev. Includes AAP data setup, PostgreSQL/Redis containers, web and task containers. Validates setclusters, syncdata commands and verifies database objects (Currency, SyncJob, AAPUser counts) using pytest."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manual CI Test Trigger for Container Images (Priority: P1)

As a DevOps engineer or release manager, I need to manually trigger integration tests against specific container image versions to verify they work correctly before promoting to production.

**Why this priority**: This is the core value proposition - enabling pre-release validation of container images against real AAP instances. Without this, we risk deploying broken images to customers.

**Independent Test**: Can be fully tested by triggering the GitHub Actions workflow with a specific image tag and verifying it completes successfully with all assertions passing.

**Acceptance Scenarios**:

1. **Given** I have a container image in quay.io, **When** I trigger the integration test workflow with image_tag=`quay.io/aap/automation-dashboard:v1.2.3` and aap_version=`2.6`, **Then** the test downloads the image, starts all containers, syncs data from AAP, and verifies database objects were created correctly
2. **Given** I build a container image locally, **When** I run the integration test script with `--image automation-dashboard:test`, **Then** the test uses my local image and validates it works correctly
3. **Given** the integration test workflow is running, **When** any step fails (AAP setup, container startup, data sync, validation), **Then** the workflow fails with clear error messages and logs are captured for debugging

---

### User Story 2 - Local Development Testing (Priority: P2)

As a developer working on the automation dashboard, I need to test my changes against a real AAP instance locally before pushing to CI to catch integration issues early.

**Why this priority**: Enables rapid development feedback loop. Developers can validate AAP integration without waiting for CI, reducing development time and CI usage.

**Independent Test**: Can be fully tested by running `./run_integration_test.sh` locally after making code changes and verifying the test passes with database validations.

**Acceptance Scenarios**:

1. **Given** I have made code changes to the syncdata logic, **When** I run `./run_integration_test.sh --aap-version 2.6`, **Then** the script sets up AAP, starts my locally built containers, and validates data synchronization works correctly
2. **Given** I want to debug a failing integration test, **When** I run the test without `--cleanup`, **Then** all containers remain running so I can inspect logs, query the database, and investigate issues
3. **Given** I have an existing AAP instance running from previous tests, **When** I run `./run_integration_test.sh --skip-aap`, **Then** the test reuses the existing AAP instance and skips the time-consuming AAP setup step

---

### User Story 3 - Multi-AAP Version Testing (Priority: P2)

As a QA engineer, I need to test the dashboard against multiple AAP versions (2.5 and 2.6) to ensure compatibility across the supported version matrix.

**Why this priority**: Automation Dashboard must support multiple AAP versions. Testing against both versions prevents version-specific bugs from reaching customers.

**Independent Test**: Can be fully tested by running the integration test with `--aap-version 2.5` and `--aap-version 2.6` separately and verifying both pass.

**Acceptance Scenarios**:

1. **Given** I need to validate AAP 2.5 compatibility, **When** I trigger the integration test with `aap_version=2.5`, **Then** the test starts AAP 2.5 instance on port 44925, creates test data, and validates synchronization works
2. **Given** I need to validate AAP 2.6 compatibility, **When** I trigger the integration test with `aap_version=2.6`, **Then** the test starts AAP 2.6 instance on port 44926, creates test data, and validates synchronization works
3. **Given** I need comprehensive version testing, **When** I run both AAP 2.5 and 2.6 tests sequentially, **Then** both tests pass independently without interference

---

### User Story 4 - Database Object Validation with pytest (Priority: P1)

As a developer, I need automated pytest validation to verify that data synchronization creates the correct database objects so I can catch data integrity issues early.

**Why this priority**: Critical for ensuring data synchronization works correctly. Without automated validation, we'd need manual database inspection which is error-prone and time-consuming.

**Independent Test**: Can be fully tested by running the pytest validation script after data sync and verifying it checks Currency, SyncJob, and AAPUser object counts match expected values.

**Acceptance Scenarios**:

1. **Given** data has been synchronized from AAP, **When** the pytest validation script runs, **Then** it verifies at least 5 Currency objects exist (for different currencies)
2. **Given** data has been synchronized from AAP, **When** the pytest validation script runs, **Then** it verifies at least 2 SyncJob objects exist (one for sync_jobs, one for parse tasks)
3. **Given** data has been synchronized from AAP, **When** the pytest validation script runs, **Then** it verifies at least 1 AAPUser object exists representing the admin user from AAP
4. **Given** the validation finds insufficient or incorrect objects, **When** the pytest script completes, **Then** it fails the test with clear assertion messages indicating what was expected vs actual

---

### Edge Cases

- What happens when AAP instance fails to start or becomes unavailable during the test?
  - Test should fail gracefully with clear error message and cleanup resources
  
- How does the system handle network timeouts when connecting to AAP?
  - Test should have reasonable timeouts (600s for AAP startup) and fail with timeout error message

- What happens when the container image is corrupted or missing required files?
  - Test should fail during container startup with clear error about what's missing

- How does the test handle database migration failures?
  - Test should catch migration errors and fail with database error logs

- What happens if AAP returns unexpected API responses or schema changes?
  - Test should fail during data sync with error indicating AAP API issue

- How does the test handle port conflicts if services are already running?
  - Docker compose should fail with port conflict error, requiring user to stop conflicting services

- What happens when disk space is insufficient for AAP or database?
  - Test should fail with disk space error during AAP or database startup

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support manual trigger of integration tests via GitHub Actions workflow with configurable parameters (image_tag, aap_version)
- **FR-002**: System MUST support testing of container images from both external registries (quay.io) and locally built images, with optional authentication via environment variables and anonymous fallback
- **FR-003**: System MUST automatically setup AAP instance using aap-dev repository (versions 2.5 or 2.6)
- **FR-004**: System MUST retrieve AAP admin password and URL automatically from aap-dev
- **FR-005**: System MUST create test data in AAP using the existing `setup_aap.py` script (organizations, projects, job templates, jobs, users)
- **FR-006**: System MUST start PostgreSQL 15 container with health checks and proper initialization
- **FR-007**: System MUST start Redis container with health checks
- **FR-008**: System MUST start two separate containers from the dashboard image: web container (Django + Nginx) and task container (Celery worker)
- **FR-009**: System MUST execute `setclusters` management command with AAP connection details
- **FR-010**: System MUST execute `syncdata` management command to trigger data synchronization from AAP
- **FR-011**: System MUST wait for task container to retrieve and parse data from AAP before validation by polling database for SyncJob completion status every 5 seconds with 300-second timeout
- **FR-012**: System MUST validate database objects using pytest, checking minimum counts: Currency ≥5, SyncJob ≥2, AAPUser ≥1
- **FR-013**: System MUST support local test execution via bash script (`run_integration_test.sh`)
- **FR-014**: System MUST provide structured logging with phase markers ([PHASE] prefix), timing metrics for each phase, and detailed error context for debugging failed tests
- **FR-015**: System MUST support cleanup mode to remove all resources after test completion
- **FR-016**: System MUST support skip-aap mode to reuse existing AAP instance for faster test iterations
- **FR-017**: System MUST capture container logs on test failure for debugging
- **FR-018**: Test MUST complete within reasonable time (< 25 minutes total, < 20 minutes typical)
- **FR-019**: System MUST log success indicators including object counts, sync job status, and API endpoint responses for validation and reliability tracking

### Key Entities *(include if feature involves data)*

- **Test Environment**: Consists of AAP instance, PostgreSQL, Redis, web container, task container running together in isolated network
- **AAP Instance**: Real AAP installation (2.5 or 2.6) with test data (orgs, projects, templates, jobs, users)
- **Container Image**: The automation-dashboard Docker image being tested, sourced from registry or built locally
- **Test Data**: AAP objects created by setup_aap.py including 2+ organizations, 3+ job templates, 4+ jobs, 2+ labels
- **Database Objects**: Currency, SyncJob, AAPUser Django model instances created during data synchronization
- **Validation Script**: pytest-based Python script that queries database and asserts expected object counts

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can trigger integration test manually in GitHub Actions and receive results within 20 minutes
- **SC-002**: Integration test successfully validates container images from both quay.io registry and local builds
- **SC-003**: Test catches AAP integration failures with 100% reliability (any sync error causes test failure)
- **SC-004**: Database validation detects missing or incorrect object counts with clear error messages
- **SC-005**: Test works reliably with both AAP 2.5 and AAP 2.6 versions
- **SC-006**: Developers can run full integration test locally with single command
- **SC-007**: Test provides clear failure diagnostics including container logs and database state
- **SC-008**: Integration test can be executed at least 10 times consecutively without failures (reliability metric)
- **SC-009**: Test completes successfully on both x86_64 and aarch64 architectures
- **SC-010**: 95% of integration test runs complete without infrastructure failures (AAP, network, disk issues)

## Assumptions

- AAP-dev repository (https://github.com/ansible/aap-dev) remains available and functional for AAP 2.5 and 2.6
- Docker or Podman is available in CI environment and on developer machines
- Internet connectivity is available for downloading AAP images and dependencies
- Sufficient disk space (~10GB) is available for AAP, containers, and databases
- Python 3.12+ is available for running setup scripts
- Git is available for cloning aap-dev repository
- Test execution environment has at least 4GB RAM available
- setup_aap.py script continues to work with current AAP API versions
- Existing database models (Currency, SyncJob, AAPUser) remain stable
- setclusters and syncdata management commands maintain current interfaces

## Out of Scope

- Performance benchmarking or load testing of container images
- Testing of horizontal scaling or multi-instance deployments
- UI/frontend integration testing (covered by separate Playwright tests)
- Security penetration testing or vulnerability scanning
- Testing of backup/restore procedures
- Testing of upgrade paths between dashboard versions
- Testing of non-Linux operating systems
- Testing of custom AAP configurations or third-party integrations
- Automated scheduling of integration tests (manual trigger only)
- Testing of installer (bundled or online variants)

## Dependencies

- **External**: aap-dev repository must be accessible and functional
- **External**: Docker/Podman container runtime
- **External**: Python 3.12+ with requests and pyyaml packages
- **External**: Git for repository cloning
- **External**: Internet connectivity for image pulls and AAP setup
- **Internal**: setup_aap.py script in src/backend/tests/mock_aap/
- **Internal**: Docker/Dockerfile.backend must produce working container image
- **Internal**: Management commands (setclusters, syncdata) must be functional
- **Internal**: Database models (Currency, SyncJob, AAPUser) must be defined
- **Internal**: Existing docker-compose infrastructure if used
- **External**: Optional registry credentials via environment variables (REGISTRY_QUAY_IO_USERNAME/PASSWORD) for private images; anonymous access used as fallback for public images

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| AAP-dev breaks or becomes unavailable | High - tests cannot run | Pin aap-dev to specific commit; maintain local mirror; document manual AAP setup as fallback |
| AAP startup is slow (>10 minutes) | Medium - long test times | Implement skip-aap mode for local development; cache AAP state when possible |
| Network issues downloading images | Medium - flaky tests | Add retry logic; use local registry mirrors in CI; fail fast with clear errors |
| Port conflicts on developer machines | Low - local tests fail | Document port requirements; provide script to check/kill conflicting services |
| Disk space exhaustion | Medium - test failures | Add disk space checks before test; auto-cleanup old AAP instances; document requirements |
| AAP API changes break setup_aap.py | High - tests fail incorrectly | Pin AAP versions; add API version detection; maintain compatibility layer |
| Database migrations fail | High - tests unusable | Test migrations separately; add migration validation step; fail fast with clear error |

## Clarifications

### Session 2026-01-22

- Q: What are the expected minimum counts for Currency, SyncJob, and AAPUser objects in validation? → A: Currency ≥5, SyncJob ≥2, AAPUser ≥1 (based on setup_aap.py test data)
- Q: How should the test handle registry authentication for pulling images from quay.io? → A: Use environment variables/secrets for credentials with fallback to anonymous access (CI uses GitHub secrets, local uses optional env vars, fallback to public pull)
- Q: Should we standardize the image reference format in examples? → A: Yes, use full registry format [registry/][namespace/]name:tag (e.g., quay.io/aap/automation-dashboard:v1.2.3, automation-dashboard:test for local)
- Q: What logging/metrics should be captured during test execution for observability? → A: Structured logging with phase markers ([PHASE] prefix), timing metrics for each phase, error context (container logs, DB state, AAP responses), and success indicators (object counts, sync status)
- Q: How should the test determine when data synchronization is complete? → A: Poll database for SyncJob completion status every 5 seconds, wait for status='completed', timeout after 300 seconds (5 minutes), fail with clear message on timeout or error

## Open Questions

None - feature requirements are clear based on existing integration test implementation.
