<!--
Sync Impact Report - Constitution v1.0.0
================================================================================
Version Change: INITIAL → 1.0.0
Rationale: Initial constitution establishment for Automation Dashboard project

Principles Established:
  1. Security-First Development (OAuth2, encryption, audit logging)
  2. Containerized Deployment (Docker, Ansible automation)
  3. Comprehensive Testing (unit, integration, E2E with real AAP)
  4. Automated Quality Gates (pre-commit, CI/CD, requirements sync)
  5. Documentation Standards (architecture docs, API specs, deployment guides)

Templates Status:
  ✅ plan-template.md - Aligned with testing requirements
  ✅ spec-template.md - Includes security and testing sections
  ✅ tasks-template.md - Supports containerized deployment tasks
  ⚠  commands/*.md - To be reviewed for AAP-specific terminology

Follow-up Items:
  - Review command templates for consistency with AAP terminology
  - Establish SLA/performance benchmarks for sync operations
  - Define formal change management process for breaking API changes

Generated: 2026-01-22
-->

# Automation Dashboard Constitution

## Core Principles

### I. Security-First Development

All features and integrations MUST implement security by design. This principle is NON-NEGOTIABLE.

**Requirements**:
- OAuth2 authentication for all AAP cluster integrations
- Encrypted storage of sensitive credentials (tokens, client secrets)
- TLS/HTTPS for all external communications
- Role-based access control for API endpoints
- Audit logging for security-relevant events
- Regular security dependency updates via automated tools

**Rationale**: The Automation Dashboard handles sensitive AAP credentials and job execution data. Security breaches could expose customer automation workflows and infrastructure details. Defense-in-depth is essential.

### II. Containerized Deployment

All deployments MUST use containerized architecture with Ansible automation.

**Requirements**:
- Docker containers for all services (web, task worker, database, cache)
- Ansible-based installer with both online and bundled variants
- Non-root container execution
- Health checks for all services
- Support for both x86_64 and aarch64 architectures
- PostgreSQL 15+ and Redis 6+ as required services

**Rationale**: Containerization ensures consistent deployment across environments, simplifies dependency management, and enables horizontal scaling. Ansible automation provides reproducible installations for enterprise customers.

### III. Comprehensive Testing

All code changes MUST include appropriate test coverage before merge.

**Testing Tiers** (all mandatory):
1. **Unit Tests**: pytest for Python backend, Jest for React frontend
2. **Integration Tests**: Real AAP integration tests using aap-dev
3. **API Tests**: REST endpoint validation and contract testing
4. **E2E Tests**: Playwright for critical user workflows

**Requirements**:
- Unit tests for all business logic and data processing
- Integration tests for AAP synchronization workflows
- API tests for all REST endpoints
- E2E tests for authentication flows and report generation
- Tests MUST pass in CI before merge
- Code coverage reporting (target: >80% for critical paths)

**Rationale**: The dashboard synchronizes critical job data from AAP. Bugs can lead to incorrect cost analysis, missing data, or failed synchronizations. Comprehensive testing catches issues before production deployment.

### IV. Automated Quality Gates

All code MUST pass automated quality checks before merge.

**Pre-commit Hooks**:
- Requirements synchronization (requirements-pinned.txt → requirements-build.txt)
- Code formatting and linting
- Type checking (mypy for Python, TypeScript strict mode)

**CI/CD Gates**:
- All tests must pass (unit, integration, E2E)
- Requirements files must be in sync
- Container images must build successfully
- SonarQube code quality checks
- Security vulnerability scanning

**Rationale**: Automated gates prevent common errors, maintain code quality, and ensure dependency consistency. Manual review cannot catch all issues; automation provides consistent enforcement.

### V. Documentation Standards

All features MUST include comprehensive documentation before merge.

**Required Documentation**:
- Architecture diagrams for new components (Mermaid format)
- API endpoint documentation (OpenAPI/Swagger)
- Deployment guides for new services or configuration
- Inline code comments for complex logic
- README updates for new features
- Troubleshooting guides for error scenarios

**Location Standards**:
- `/docs/` for architecture and system documentation
- `/tests/integration/README.md` for integration test procedures
- Inline docstrings for all public APIs
- `setup/README.md` for installation procedures

**Rationale**: The Automation Dashboard is a complex system with multiple services, AAP integrations, and deployment variants. Without comprehensive documentation, onboarding is difficult and troubleshooting becomes guesswork.

## Technology Stack Standards

### Backend Requirements

**Mandatory**:
- Python 3.12+ (no support for older versions)
- Django 5.2+ with Django REST Framework
- PostgreSQL 15+ (primary database)
- Redis 6+ (caching and task queuing)
- pytest for testing framework

**Dependency Management**:
- pip-tools for requirements compilation
- requirements-pinned.txt as source of truth
- Automated sync via make sync-requirements
- Vulnerability scanning via GitHub Dependabot

### Frontend Requirements

**Mandatory**:
- React 18+ with TypeScript strict mode
- PatternFly 5+ for UI components
- Redux Toolkit for state management
- Vite for build tooling
- Playwright for E2E testing

### Container Requirements

**Mandatory**:
- UBI9 minimal base images
- Multi-stage builds (frontend + backend)
- Non-root user execution (uid 1000)
- Health check endpoints
- Proper signal handling (dumb-init)

## Development Workflow

### Change Management Process

1. **Feature Planning**:
   - Create spec in `.specify/features/<feature-name>/spec.md`
   - Include user scenarios and testing approach
   - Get approval before implementation

2. **Implementation**:
   - Create feature branch from `main`
   - Implement with test coverage
   - Follow security and documentation principles
   - Run pre-commit hooks

3. **Review**:
   - All PRs require code review
   - CI checks must pass
   - Security review for authentication/authorization changes
   - Documentation review for user-facing features

4. **Deployment**:
   - Merge to `main` triggers image build
   - Tag releases with semantic versioning (vX.Y.Z)
   - Bundled installer generated for tagged releases
   - Release notes document breaking changes

### Breaking Changes Policy

**Definition**: A breaking change is any modification that:
- Changes API response structure or field names
- Modifies database schema without backward compatibility
- Changes configuration file format
- Alters authentication or authorization behavior
- Removes or renames CLI commands

**Requirements**:
- MUST bump MAJOR version number
- MUST document migration procedure
- MUST provide deprecation warnings in prior MINOR release (when feasible)
- MUST update all affected documentation

### Dependency Updates

**Automated**:
- Dependabot PRs for security vulnerabilities (reviewed within 48 hours)
- Pre-commit hooks sync requirements files automatically

**Manual**:
- Major version upgrades require testing plan
- Database version upgrades require migration testing
- Python version upgrades require full test suite validation

## Governance

### Constitution Authority

This constitution supersedes all other development practices and guidelines. In case of conflict between this document and other documentation, this constitution takes precedence.

### Amendment Process

1. **Proposal**: Document proposed changes with rationale
2. **Review**: Discuss impact on existing features and templates
3. **Approval**: Requires maintainer consensus
4. **Migration**: Update templates and propagate changes to docs
5. **Version Bump**:
   - MAJOR: Backward-incompatible principle changes
   - MINOR: New principles or expanded sections
   - PATCH: Clarifications, typo fixes, non-semantic changes

### Compliance Review

- All PRs MUST verify constitution compliance
- Security changes require explicit security principle check
- Breaking changes require version bump verification
- New features require testing principle compliance

### Exception Handling

Exceptions to these principles require:
1. Documented technical justification
2. Maintainer approval
3. Time-bound scope (temporary exceptions expire)
4. Migration plan to achieve compliance

**Version**: 1.0.0 | **Ratified**: 2026-01-22 | **Last Amended**: 2026-01-22
