# Research: AAP Instance Setup (Phase 1)

**Date**: 2026-01-26  
**Spec**: [spec-phase1-aap-setup.md](spec-phase1-aap-setup.md)  
**Plan**: [plan-phase1-aap-setup.md](plan-phase1-aap-setup.md)

## Research Questions

### Q1: How does aap-dev repository work and what commands start AAP?

**Decision**: Use aap-dev's make targets for AAP lifecycle management

**Rationale**:
- aap-dev provides standardized make target: `make aap` (alias for `make skaffold-dev`)
- Version selection via `AAP_VERSION` environment variable (2.5-next or 2.6)
- Automatically handles container orchestration, network setup, and port mapping via Skaffold
- Well-maintained by Ansible team with documentation
- Admin password retrieved from ~/.aap-dev/admin_password.txt via `make admin-password`

**Implementation Details**:
```bash
# Clone aap-dev
git clone https://github.com/ansible/aap-dev.git
cd aap-dev

# Checkout specific version if needed
git checkout ${AAP_DEV_VERSION:-main}

# Start AAP 2.6 (default port 44926, default version)
export AAP_VERSION=2.6
make aap

# Start AAP 2.5 (port 44925)
export AAP_VERSION=2.5-next
make aap
```

**Alternatives Considered**:
- Manual docker-compose: Rejected - aap-dev already provides this abstraction
- Direct podman commands: Rejected - harder to maintain across AAP versions

---

### Q2: How to retrieve AAP admin password from aap-dev?

**Decision**: Use aap-dev's `make admin-password` command to retrieve password

**Rationale**:
- aap-dev provides `make admin-password` target that queries password from Kubernetes secret
- Password is stored in K8s secret created during AAP deployment (NOT in a pre-existing file)
- The `.tmp/admin-password` file may exist if someone cached the output via `make admin-password > .tmp/admin-password`, but it's not the source
- Using the make target queries K8s directly and is always current
- Consistent across AAP versions

**Implementation Details**:
```bash
# Use aap-dev make target (queries K8s secret)
cd aap-dev
AAP_PASSWORD=$(make admin-password)

# Username is always 'admin'
AAP_USERNAME="admin"

# Note: Do NOT read from .tmp/admin-password file - it doesn't pre-exist.
# It's only created if someone manually runs: make admin-password > .tmp/admin-password
```

**Alternatives Considered**:
- Parse make command output: Rejected - fragile, depends on output format
- Extract from container environment: Rejected - requires container inspection
- User provides password: Rejected - defeats automation purpose

---

### Q3: What health check endpoint should be used for AAP readiness?

**Decision**: Use version-specific endpoint determined by known AAP_VERSION

**Rationale**:
- AAP version is known from setup (FR-001, --aap-version parameter), not discovered
- AAP 2.4: Uses `/api/v2/ping/` (AWX-style API)
- AAP 2.5+: Uses `/api/gateway/v1/ping/` (new gateway architecture)
- Both endpoints return 200 OK when AAP is fully ready
- Response includes version information for validation
- No authentication required for ping endpoints
- Since version is known, endpoint selection is deterministic (no fallback logic needed)

**Implementation Details**:
```bash
# Deterministic endpoint selection based on known AAP_VERSION
if [[ "$AAP_VERSION" == "2.5-next" || "$AAP_VERSION" == "2.6" ]]; then
    HEALTH_ENDPOINT="/api/gateway/v1/ping/"
else
    # AAP 2.4
    HEALTH_ENDPOINT="/api/v2/ping/"
fi

# Check health
if curl -s -f -k "${AAP_URL}${HEALTH_ENDPOINT}" >/dev/null 2>&1; then
    echo "AAP is ready"
else
    echo "AAP not ready yet"
    return 1
fi
```

**Alternatives Considered**:
- Check specific API endpoints (/api/v2/organizations/): Rejected - requires auth
- Poll for specific services: Rejected - too granular, slower
- Check container status only: Rejected - containers may be up but API not ready

---

### Q4: How to generate aap_access.json with correct URL parsing?

**Decision**: Parse AAP_URL components using bash string manipulation

**Rationale**:
- AAP_URL format: `http://hostname:port` or `https://hostname:port`
- Need to extract: protocol, hostname, port for aap_access.json
- Bash string operations are sufficient (no need for external tools)
- Matches setup_aap.py parsing logic

**Implementation Details**:
```bash
# Parse AAP_URL
AAP_PROTOCOL=$(echo "$AAP_URL" | cut -d':' -f1)  # http or https
AAP_HOST_PORT=$(echo "$AAP_URL" | sed 's|^https\?://||')  # hostname:port
AAP_ADDRESS=$(echo "$AAP_HOST_PORT" | cut -d':' -f1)  # hostname
AAP_PORT=$(echo "$AAP_HOST_PORT" | cut -d':' -f2)  # port

# Generate JSON
cat > aap_access.json <<EOF
{
    "client_id": null,
    "client_secret": null,
    "access_token": null,
    "refresh_token": null,
    "aap_url": "${AAP_URL}",
    "aap_protocol": "${AAP_PROTOCOL}",
    "aap_address": "${AAP_ADDRESS}",
    "aap_port": "${AAP_PORT}",
    "aap_version": "${AAP_VERSION}",
    "aap_password": "${AAP_PASSWORD}"
}
EOF
```

**Alternatives Considered**:
- Use jq for JSON generation: Rejected - adds dependency
- Use Python script: Rejected - want pure bash solution for Phase 1
- Call setup_aap.py: Rejected - that's Phase 2 (requires test data)

---

### Q5: What disk space check is sufficient for AAP requirements?

**Decision**: Check 10GB free in both /tmp and current directory using df

**Rationale**:
- AAP containers use /tmp for temporary files
- aap-dev repository cloned to current directory (~500MB)
- AAP images require ~8GB download + storage
- 10GB threshold provides safety margin
- df command available on all Linux systems

**Implementation Details**:
```bash
# Check disk space function
check_disk_space() {
    local path=$1
    local required_gb=10
    
    # Get available space in GB
    local available_gb=$(df -BG "$path" | awk 'NR==2 {print $4}' | tr -d 'G')
    
    if [ "$available_gb" -lt "$required_gb" ]; then
        echo "ERROR: Insufficient disk space in $path"
        echo "  Required: ${required_gb}GB, Available: ${available_gb}GB"
        return 1
    fi
    
    echo "Disk space OK: ${available_gb}GB available in $path"
    return 0
}

# Check both locations
check_disk_space /tmp || exit 1
check_disk_space "$(pwd)" || exit 1
```

**Alternatives Considered**:
- Check only system root: Rejected - might not reflect actual usage locations
- Use du to measure exact AAP size: Rejected - slow, not needed for upfront check
- Skip check entirely: Rejected - disk full errors are hard to debug

---

## Technology Decisions

### Bash vs Python for Orchestration

**Decision**: Use Bash for Phase 1 orchestration script

**Rationale**:
- Simple script logic (no complex data structures)
- Direct integration with aap-dev make commands
- No additional runtime dependencies (Python already needed for later phases)
- Fast execution for developer workflow
- Easy to debug with set -x

**Future**: Phase 2+ may use Python for data setup (complex AAP API interactions)

### Container Runtime Detection

**Decision**: Auto-detect Docker or Podman, prefer Docker

**Rationale**:
- aap-dev supports both Docker and Podman
- Most developers have Docker
- Podman common on RHEL systems
- Auto-detection provides best compatibility

**Implementation**:
```bash
# Detect container runtime
if command -v docker &> /dev/null; then
    CONTAINER_RUNTIME="docker"
elif command -v podman &> /dev/null; then
    CONTAINER_RUNTIME="podman"
else
    echo "ERROR: Neither docker nor podman found"
    exit 1
fi
```

---

## Open Questions

None - all Phase 1 technical decisions are resolved.

## Summary

Phase 1 research confirms:
- ✅ aap-dev provides all needed AAP lifecycle management
- ✅ Admin password accessible via ~/.aap-dev/admin_password.txt
- ✅ Health check endpoints well-defined for all AAP versions
- ✅ aap_access.json can be generated with bash string manipulation
- ✅ Disk space checks straightforward with df command
- ✅ Bash is appropriate for Phase 1 orchestration

**Ready to proceed to implementation.**
