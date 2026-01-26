# Feature Specification: AAP Instance Setup (Phase 1)

**Feature Branch**: `001-container-image-test`  
**Created**: 2026-01-26  
**Status**: In Progress - Phase 1 Only  
**Phase**: AAP Instance Setup using aap-dev

## Overview

This is Phase 1 of the container image integration test feature. Focus: **Setup AAP instance using aap-dev and validate it's running correctly**.

**Later phases** (not in this spec):
- Phase 2: Fill AAP with test data
- Phase 3: Container setup and data sync
- Phase 4: Database validation

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Local AAP Instance Setup (Priority: P1)

As a developer, I need to automatically setup a working AAP instance using aap-dev so I can test integration with the automation dashboard.

**Why this priority**: Without a working AAP instance, no integration testing is possible. This is the foundation for all other phases.

**Independent Test**: Run setup script, verify AAP instance starts, verify admin credentials work, verify API is accessible.

**Acceptance Scenarios**:

1. **Given** I have aap-dev repository cloned, **When** I run the AAP setup script with `--aap-version 2.6`, **Then** AAP 2.6 instance starts on port 44926, admin password is retrieved, and API responds to health check
2. **Given** I want to test with AAP 2.5, **When** I run the AAP setup script with `--aap-version 2.5`, **Then** AAP 2.5 instance starts on port 44925, admin password is retrieved, and API responds to health check
3. **Given** AAP instance failed to start, **When** the setup script detects failure, **Then** it fails with clear error message, comprehensive diagnostics (container logs, disk space, port status, network checks), and debugging guidance with next troubleshooting steps
4. **Given** I have an existing AAP instance running, **When** I run the setup script with `--skip-aap`, **Then** the script reuses the existing instance and skips setup

---

### User Story 2 - AAP Instance Cleanup (Priority: P2)

As a developer, I need to cleanup AAP instances after testing to free up resources and avoid port conflicts.

**Why this priority**: Important for developer workflow but not blocking for initial testing.

**Independent Test**: Run cleanup script, verify AAP instance stops, verify ports are freed.

**Acceptance Scenarios**:

1. **Given** AAP instance is running, **When** I run cleanup script, **Then** AAP instance stops and all resources are freed
2. **Given** multiple AAP versions are running, **When** I run cleanup with specific version, **Then** only that version stops

---

### Edge Cases

- What happens when aap-dev repository is unavailable?
  - Setup should fail with clear error message about repository access
  
- What happens when port 44926 is already in use?
  - Setup should detect port conflict and fail with helpful message

- What happens when AAP takes too long to start (>10 minutes)?
  - Setup should timeout with clear message and show AAP logs

- What happens when AAP fails health check?
  - Setup should retry health check continuously every 5 seconds for up to 600 seconds (120 attempts), then fail with diagnostic info

- What happens when disk space is insufficient?
  - Setup should fail early with disk space error

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support AAP version selection (2.5 or 2.6) via command-line parameter
- **FR-002**: System MUST automatically clone/update aap-dev repository from https://github.com/ansible/aap-dev
- **FR-003**: System MUST support --aap-dev-version parameter to specify git commit SHA, branch name, or git tag for aap-dev repository checkout (defaults to main branch if not specified)
- **FR-004**: System MUST start AAP instance on correct port (44925 for AAP 2.5, 44926 for AAP 2.6)
- **FR-005**: System MUST retrieve AAP admin password automatically from aap-dev output
- **FR-006**: System MUST retrieve AAP URL automatically from aap-dev output
- **FR-007**: System MUST validate AAP instance is running via health check endpoint (/api/v2/ping/) with continuous polling every 5 seconds until success or 600-second timeout (120 attempts maximum)
- **FR-008**: System MUST wait for AAP to be fully ready (timeout 600 seconds)
- **FR-009**: System MUST provide structured logging with [PHASE] markers for AAP setup steps
- **FR-010**: System MUST support --skip-aap mode to reuse existing AAP instance
- **FR-011**: System MUST support --cleanup mode to stop AAP instance and free resources
- **FR-012**: System MUST capture comprehensive diagnostic information on setup failure: container logs from all AAP containers, disk space info, port status, network connectivity checks, and aap-dev console output
- **FR-013**: System MUST provide debugging guidance on failure including: commands to inspect running containers, location of aap-dev documentation, how to access aap-dev logs, and common troubleshooting steps
- **FR-014**: System MUST export AAP_URL and AAP_PASSWORD as environment variables for later phases
- **FR-015**: System MUST generate aap_access.json file with structure matching setup_aap.py output: `{client_id, client_secret, access_token, refresh_token, aap_url, aap_protocol, aap_address, aap_port, aap_version, aap_password}` where Phase 1 populates `{aap_url, aap_protocol, aap_address, aap_port, aap_version, aap_password}` and sets OAuth2/token fields to null for later phases
- **FR-016**: System MUST validate disk space before starting AAP with minimum 10GB free in /tmp directory and current directory (where aap-dev will be cloned)
- **FR-017**: System MUST validate required tools are available (docker/podman, git, curl)

### Key Entities *(include if feature involves data)*

- **AAP Instance**: Running Ansible Automation Platform (version 2.5 or 2.6) accessible via HTTP API
- **AAP Credentials**: Admin username (typically 'admin') and password retrieved from aap-dev
- **AAP URL**: Base URL for accessing AAP API (e.g., http://localhost:44926)
- **aap-dev Repository**: GitHub repository containing AAP development environment setup; can be checked out to specific commit SHA, branch name, or git tag via --aap-dev-version parameter
- **Health Status**: AAP readiness state determined by /api/v2/ping/ endpoint response
- **aap_access.json**: JSON file containing AAP connection details with fields: `client_id` (null in Phase 1), `client_secret` (null), `access_token` (null), `refresh_token` (null), `aap_url` (e.g., "http://localhost:44926"), `aap_protocol` ("http" or "https"), `aap_address` (hostname/IP), `aap_port` (port number as string), `aap_version` ("2.5" or "2.6"), `aap_password` (admin password from aap-dev)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developer can start AAP 2.5 or 2.6 instance with single command
- **SC-002**: AAP instance starts successfully within 10 minutes (typical), 15 minutes (maximum)
- **SC-003**: Admin credentials are automatically retrieved and validated
- **SC-004**: AAP API responds to health check with 200 status code
- **SC-005**: Setup script provides clear progress indicators for long-running operations
- **SC-006**: Setup script fails fast with clear error messages when prerequisites are missing
- **SC-007**: AAP instance can be cleaned up completely with single command
- **SC-008**: Setup works on both x86_64 and aarch64 architectures

## Assumptions

- AAP-dev repository (https://github.com/ansible/aap-dev) remains available and functional
- Docker or Podman is available on developer machine
- Internet connectivity is available for cloning repository and downloading AAP images
- Ports 44925 and 44926 are available (or can be freed)
- Sufficient disk space (~10GB) is available
- Git and curl are available in PATH

## Out of Scope

- Creating test data in AAP (Phase 2)
- Container image building or testing (Phase 3)
- Database validation (Phase 4)
- Multiple simultaneous AAP instances
- Custom AAP configurations
- AAP backup/restore
- AAP upgrade testing
- GitHub Actions integration (later phase)

## Dependencies

- **External**: aap-dev repository must be accessible
- **External**: Docker/Podman container runtime
- **External**: Git for repository cloning
- **External**: curl for health checks
- **External**: Internet connectivity

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| AAP-dev breaks or becomes unavailable | High - setup cannot work | Support --aap-dev-version parameter to pin to specific commit/tag; document recommended stable versions in README |
| AAP startup is slow (>10 minutes) | Medium - developer frustration | Add progress indicators; implement skip-aap mode for reruns |
| Network issues cloning aap-dev | Medium - flaky setup | Add retry logic; use local cache if available |
| Port conflicts on developer machine | Low - setup fails | Add port check; provide script to kill conflicting services |
| Disk space exhaustion | Medium - setup fails | Add disk space check before starting; fail fast with clear message |

## Clarifications

### Session 2026-01-26

- Q: What is the minimum scope for Phase 1? → A: AAP instance setup and validation only. No test data, no containers, no sync.
- Q: How do we validate AAP is ready? → A: Health check on /api/v2/ping/ returns 200, plus verify admin credentials work
- Q: Should we support multiple AAP versions simultaneously? → A: No, one at a time is sufficient for Phase 1
- Q: What happens to later phases? → A: Documented in separate spec files (spec-phase2-aap-data.md, spec-phase3-containers.md, etc.)
- Q: What fields should be in aap_access.json? → A: Same structure as setup_aap.py generates: {client_id, client_secret, access_token, refresh_token, aap_url, aap_protocol, aap_address, aap_port, aap_version, aap_password} where Phase 1 sets OAuth2/token fields to null and populates AAP connection fields
- Q: How should health check retries be implemented? → A: Continuous polling every 5 seconds for 600 seconds (120 attempts maximum)
- Q: Should aap-dev commit be hardcoded or configurable? → A: Use --aap-dev-version parameter accepting git commit SHA, branch name, or git tag; defaults to main branch
- Q: What AAP logs should be captured on setup failure? → A: Container logs from all AAP containers, disk space info, port status, network connectivity checks, aap-dev console output, plus debugging guidance with inspection commands and documentation links
- Q: Where should disk space be validated? → A: Validate available space in /tmp and current directory where aap-dev will be cloned

## Open Questions

None - Phase 1 scope is clear and focused.
