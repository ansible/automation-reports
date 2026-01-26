#!/usr/bin/env bash
#
# setup_aap.sh - Automatically setup AAP instance for integration testing
#
# Usage: ./setup_aap.sh [OPTIONS]
#
# Options:
#   --aap-version VERSION     AAP version to start (2.5 or 2.6, default: 2.6)
#   --aap-dev-version REF     Git ref for aap-dev checkout (commit/branch/tag, default: main)
#   --skip-aap                Skip AAP startup, reuse existing instance
#
# Output:
#   - aap_access.json: Connection configuration
#   - Environment variables: AAP_URL, AAP_PASSWORD, AAP_VERSION, AAP_USERNAME
#
# Phase 1 of 4: AAP Instance Setup only (no test data, no containers, no validation)

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AAP_VERSION_ARG="2.6"
AAP_DEV_VERSION_ARG="main"
SKIP_AAP=false
#AAP_DEV_REPO="https://github.com/ansible/aap-dev.git"
AAP_DEV_REPO="git@github.com:ansible/aap-dev.git"
AAP_DEV_DIR="${SCRIPT_DIR}/aap-dev"
AAP_ACCESS_JSON="${SCRIPT_DIR}/aap_access.json"

# Health check configuration
HEALTH_CHECK_INTERVAL=5
HEALTH_CHECK_TIMEOUT=600
HEALTH_CHECK_MAX_ATTEMPTS=$((HEALTH_CHECK_TIMEOUT / HEALTH_CHECK_INTERVAL))

# Disk space requirements (in GB)
REQUIRED_DISK_SPACE_GB=10

# =============================================================================
# Logging Functions
# =============================================================================

log_phase() {
    echo ""
    echo "========================================"
    echo "[PHASE] $*"
    echo "========================================"
}

log_info() {
    echo "[INFO] $*"
}

log_success() {
    echo "[SUCCESS] $*"
}

log_error() {
    echo "[ERROR] $*" >&2
}

log_warning() {
    echo "[WARNING] $*"
}

# =============================================================================
# Argument Parsing
# =============================================================================

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --aap-version)
                AAP_VERSION_ARG="$2"
                shift 2
                ;;
            --aap-dev-version)
                AAP_DEV_VERSION_ARG="$2"
                shift 2
                ;;
            --skip-aap)
                SKIP_AAP=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Validate AAP version
    if [[ ! "$AAP_VERSION_ARG" =~ ^(2\.5|2\.6)$ ]]; then
        log_error "Invalid AAP version: $AAP_VERSION_ARG (must be 2.5 or 2.6)"
        exit 1
    fi
}

show_usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Setup AAP instance for integration testing.

OPTIONS:
    --aap-version VERSION     AAP version to start (2.5 or 2.6, default: 2.6)
    --aap-dev-version REF     Git ref for aap-dev (commit/branch/tag, default: main)
    --skip-aap                Skip AAP startup, reuse existing instance
    -h, --help                Show this help message

EXAMPLES:
    # Start AAP 2.6 (default)
    ./setup_aap.sh

    # Start AAP 2.5
    ./setup_aap.sh --aap-version 2.5

    # Use specific aap-dev version
    ./setup_aap.sh --aap-dev-version v2.6.1

    # Reuse existing AAP instance
    ./setup_aap.sh --skip-aap

EOF
}

# =============================================================================
# Prerequisites Check
# =============================================================================

check_prerequisites() {
    log_phase "Prerequisites Check"
    
    local missing_tools=()
    
    # Check for container runtime
    if command -v docker &> /dev/null; then
        CONTAINER_RUNTIME="docker"
        log_info "Docker found: $(command -v docker)"
    elif command -v podman &> /dev/null; then
        CONTAINER_RUNTIME="podman"
        log_info "Podman found: $(command -v podman)"
    else
        missing_tools+=("docker or podman")
    fi
    
    # Check for required tools
    for tool in git curl jq; do
        if command -v "$tool" &> /dev/null; then
            log_info "$tool found: $(command -v "$tool")"
        else
            missing_tools+=("$tool")
        fi
    done
    
    # Report missing tools
    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error ""
        log_error "Installation commands:"
        log_error "  Ubuntu/Debian: sudo apt install ${missing_tools[*]}"
        log_error "  Fedora/RHEL:   sudo dnf install ${missing_tools[*]}"
        return 1
    fi
    
    log_success "All prerequisites met"
    return 0
}

# =============================================================================
# Disk Space Check
# =============================================================================

check_disk_space() {
    local path=$1
    local location_name=$2
    
    # Get available space in GB
    local available_gb
    available_gb=$(df -BG "$path" 2>/dev/null | awk 'NR==2 {print $4}' | tr -d 'G')
    
    if [ -z "$available_gb" ]; then
        log_error "Failed to check disk space for $path"
        return 1
    fi
    
    if [ "$available_gb" -lt "$REQUIRED_DISK_SPACE_GB" ]; then
        log_error "Insufficient disk space in $location_name ($path)"
        log_error "  Required: ${REQUIRED_DISK_SPACE_GB}GB"
        log_error "  Available: ${available_gb}GB"
        log_error ""
        log_error "Solutions:"
        log_error "  - Clean Docker images: docker system prune -a"
        log_error "  - Move to filesystem with more space"
        log_error "  - Free up space in $path"
        return 1
    fi
    
    log_info "Disk space OK in $location_name: ${available_gb}GB available"
    return 0
}

check_all_disk_space() {
    log_phase "Disk Space Check"
    
    check_disk_space "/tmp" "/tmp directory" || return 1
    check_disk_space "$SCRIPT_DIR" "current directory" || return 1
    
    log_success "Sufficient disk space available"
    return 0
}

# =============================================================================
# Port Check
# =============================================================================

check_port() {
    log_phase "Port Availability Check"
    # TODO do not complain if already used by existing AAP instance we only try to start again
    return 0
    
    local port
    if [[ "$AAP_VERSION_ARG" == "2.5" ]]; then
        port=44925
    else
        port=44926
    fi
    
    # Check if port is in use
    if ss -tuln 2>/dev/null | grep -q ":${port} " || netstat -tuln 2>/dev/null | grep -q ":${port} "; then
        log_error "Port $port is already in use"
        log_error ""
        log_error "Find process using port:"
        log_error "  sudo lsof -i :$port"
        log_error "  ss -tlnp | grep $port"
        log_error ""
        log_error "Solutions:"
        log_error "  - Stop existing AAP: ./cleanup_aap.sh --force"
        log_error "  - Kill process: sudo kill <PID>"
        return 1
    fi
    
    log_info "Port $port is available"
    log_success "Port check passed"
    return 0
}

# =============================================================================
# AAP-Dev Repository Management
# =============================================================================

setup_aap_dev_repo() {
    log_phase "AAP-Dev Repository Setup"
    
    if [ -d "$AAP_DEV_DIR/.git" ]; then
        log_info "aap-dev repository already exists, updating..."
        cd "$AAP_DEV_DIR"
        git fetch origin || {
            log_warning "Failed to fetch updates, continuing with existing repository"
        }
    else
        log_info "Cloning aap-dev repository from $AAP_DEV_REPO"
        log_info "This may take a few minutes (~500MB)..."
        
        git clone "$AAP_DEV_REPO" "$AAP_DEV_DIR" || {
            log_error "Failed to clone aap-dev repository"
            log_error "Check network connectivity and repository access"
            return 1
        }
        cd "$AAP_DEV_DIR"
    fi
    
    # Checkout specified version
    if [[ "$AAP_DEV_VERSION_ARG" != "main" ]]; then
        log_info "Checking out aap-dev version: $AAP_DEV_VERSION_ARG"
        git checkout "$AAP_DEV_VERSION_ARG" || {
            log_error "Failed to checkout version: $AAP_DEV_VERSION_ARG"
            log_error "Version may not exist. Check available versions:"
            log_error "  git tag"
            log_error "  git branch -r"
            return 1
        }
    else
        log_info "Using aap-dev main branch"
        git checkout main || git checkout master || {
            log_error "Failed to checkout default branch"
            return 1
        }
        git pull origin || {
            log_warning "Failed to pull latest changes, using current version"
        }
    fi
    
    log_success "AAP-dev repository ready at $AAP_DEV_DIR"
    return 0
}

# =============================================================================
# AAP Instance Management
# =============================================================================

start_aap() {
    log_phase "AAP Instance Setup"
    
    cd "$AAP_DEV_DIR"
    
    # Set AAP version environment variable
    if [[ "$AAP_VERSION_ARG" == "2.5" ]]; then
        export AAP_VERSION="2.5-next"
        local expected_port=44925
    else
        export AAP_VERSION="2.6-next"
        local expected_port=44926
    fi
    
    log_info "Starting AAP $AAP_VERSION_ARG (internal version: $AAP_VERSION) on port $expected_port"
    log_info "This may take 10-15 minutes (downloading images ~8GB, starting services)..."
    log_info ""
    
    # Start AAP using make aap
    # TODO if needed, podman start 26-control-plane
    # TODO set AAP_URL before capture_diagnostics is called
    # TODO make aap does not return control until stopped, so we need to background it or use another method
    make aap &> aap_dev_startup.log &
    AAP_PID=$!
    if ! kill -0 "$AAP_PID" 2>/dev/null; then
        log_error "Failed to start AAP instance"
        capture_diagnostics
        return 1
    fi
    log_info "AAP startup running in background (PID: $AAP_PID)"
    log_info "Logs: $AAP_DEV_DIR/aap_dev_startup.log"
    # wait until string "AAP-DEV is up and ready" appears in log or timeout
    local timeout=900
    local interval=10
    local elapsed=0
    while ! grep -q "AAP-DEV is up and ready" "$AAP_DEV_DIR/aap_dev_startup.log"; do
        sleep $interval
        elapsed=$((elapsed + interval))
        if [ $elapsed -ge $timeout ]; then
            log_error "AAP startup timed out after ${timeout}s"
            capture_diagnostics
            return 1
        fi
    done
    log_info "AAP startup completed within ${elapsed}s"
    
    # Set AAP URL based on version
    export AAP_URL="http://localhost:${expected_port}"
    #
    
    log_success "AAP start command completed"
    return 0
}

# =============================================================================
# Health Check
# =============================================================================

check_aap_health() {
    log_phase "AAP Health Check"
    
    # Determine health check endpoint based on AAP version
    local health_endpoint
    if [[ "$AAP_VERSION_ARG" =~ ^2\.[56]$ ]]; then
        health_endpoint="/api/gateway/v1/ping/"
    else
        # AAP 2.4 (though not in Phase 1 scope)
        health_endpoint="/api/v2/ping/"
    fi
    
    log_info "Using health check endpoint: $health_endpoint"
    log_info "Polling every ${HEALTH_CHECK_INTERVAL}s for up to ${HEALTH_CHECK_TIMEOUT}s (${HEALTH_CHECK_MAX_ATTEMPTS} attempts)..."
    
    local attempt=0
    local start_time=$(date +%s)
    
    while [ $attempt -lt $HEALTH_CHECK_MAX_ATTEMPTS ]; do
        attempt=$((attempt + 1))
        local elapsed=$(($(date +%s) - start_time))
        
        # Try health check
        if curl -s -f -k "${AAP_URL}${health_endpoint}" >/dev/null 2>&1; then
            log_success "AAP instance is ready (attempt $attempt, ${elapsed}s elapsed)"
            return 0
        fi
        
        # Progress indicator
        if [ $((attempt % 12)) -eq 0 ]; then
            log_info "Still waiting... (attempt $attempt/${HEALTH_CHECK_MAX_ATTEMPTS}, ${elapsed}s/${HEALTH_CHECK_TIMEOUT}s)"
        fi
        
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    # Timeout reached
    log_error "Health check timeout after ${HEALTH_CHECK_TIMEOUT}s"
    log_error "AAP instance did not become ready"
    capture_diagnostics
    provide_debugging_guidance
    return 1
}

# =============================================================================
# Credentials Management
# =============================================================================

retrieve_admin_password() {
    log_phase "Admin Credentials Retrieval"
    
    cd "$AAP_DEV_DIR"
    
    log_info "Retrieving admin password from Kubernetes secret..."
    
    # Use make admin-password to query K8s secret
    export AAP_PASSWORD=$(make admin-password 2>/dev/null | tail -1)
    
    if [ -z "$AAP_PASSWORD" ]; then
        log_error "Failed to retrieve admin password"
        log_error ""
        log_error "Troubleshooting:"
        log_error "  cd $AAP_DEV_DIR"
        log_error "  make admin-password"
        return 1
    fi
    
    export AAP_USERNAME="admin"
    
    log_info "Admin username: $AAP_USERNAME"
    log_info "Admin password retrieved successfully (length: ${#AAP_PASSWORD} chars)"
    
    return 0
}

validate_admin_credentials() {
    log_info "Validating admin credentials..."
    
    # Try to access /api/v2/me/ endpoint
    local me_endpoint
    if [[ "$AAP_VERSION_ARG" =~ ^2\.[56]$ ]]; then
        me_endpoint="/api/controller/v2/me/"
    else
        me_endpoint="/api/v2/me/"
    fi
    
    if curl -s -f -k -u "${AAP_USERNAME}:${AAP_PASSWORD}" "${AAP_URL}${me_endpoint}" >/dev/null 2>&1; then
        log_success "Admin credentials validated"
        return 0
    else
        log_error "Failed to validate admin credentials"
        log_error "Endpoint: ${AAP_URL}${me_endpoint}"
        return 1
    fi
}

# =============================================================================
# Configuration Export
# =============================================================================

parse_aap_url() {
    # Parse AAP_URL into components
    AAP_PROTOCOL=$(echo "$AAP_URL" | cut -d':' -f1)
    local host_port=$(echo "$AAP_URL" | sed 's|^https\?://||')
    AAP_ADDRESS=$(echo "$host_port" | cut -d':' -f1)
    AAP_PORT=$(echo "$host_port" | cut -d':' -f2)
    
    log_info "AAP URL components:"
    log_info "  Protocol: $AAP_PROTOCOL"
    log_info "  Address: $AAP_ADDRESS"
    log_info "  Port: $AAP_PORT"
}

generate_aap_access_json() {
    log_phase "Configuration Export"
    
    parse_aap_url
    
    log_info "Generating aap_access.json..."
    
    # Generate JSON with OAuth2 fields as null (Phase 2+ will populate)
    cat > "$AAP_ACCESS_JSON" << EOF
{
  "client_id": null,
  "client_secret": null,
  "access_token": null,
  "refresh_token": null,
  "aap_url": "${AAP_URL}",
  "aap_protocol": "${AAP_PROTOCOL}",
  "aap_address": "${AAP_ADDRESS}",
  "aap_port": "${AAP_PORT}",
  "aap_version": "${AAP_VERSION_ARG}",
  "aap_password": "${AAP_PASSWORD}"
}
EOF
    
    if [ ! -f "$AAP_ACCESS_JSON" ]; then
        log_error "Failed to create aap_access.json"
        return 1
    fi
    
    log_success "Created: $AAP_ACCESS_JSON"
    
    # Verify JSON structure
    if ! jq empty "$AAP_ACCESS_JSON" 2>/dev/null; then
        log_error "Generated JSON is invalid"
        return 1
    fi
    
    log_info "Exporting environment variables..."
    log_info "  AAP_URL=$AAP_URL"
    log_info "  AAP_USERNAME=$AAP_USERNAME"
    log_info "  AAP_PASSWORD=<hidden>"
    log_info "  AAP_VERSION=$(echo "$AAP_VERSION_ARG" | tr -d '.')"
    
    log_success "Configuration exported successfully"
    return 0
}

# =============================================================================
# Skip AAP Mode
# =============================================================================

validate_existing_aap() {
    log_phase "Existing AAP Instance Validation"
    
    # Check if aap-dev directory exists
    if [ ! -d "$AAP_DEV_DIR" ]; then
        log_error "aap-dev directory not found: $AAP_DEV_DIR"
        log_error "Cannot skip AAP setup - no existing instance found"
        return 1
    fi
    
    # Check if aap_access.json exists
    if [ ! -f "$AAP_ACCESS_JSON" ]; then
        log_error "aap_access.json not found: $AAP_ACCESS_JSON"
        log_error "Cannot skip AAP setup - no existing configuration found"
        return 1
    fi
    
    # Load configuration
    export AAP_URL=$(jq -r '.aap_url' "$AAP_ACCESS_JSON")
    export AAP_PASSWORD=$(jq -r '.aap_password' "$AAP_ACCESS_JSON")
    export AAP_USERNAME="admin"
    local stored_version=$(jq -r '.aap_version' "$AAP_ACCESS_JSON")
    
    log_info "Found existing AAP instance:"
    log_info "  URL: $AAP_URL"
    log_info "  Version: $stored_version"
    
    # Check if AAP is reachable
    local health_endpoint
    if [[ "$stored_version" =~ ^2\.[56]$ ]]; then
        health_endpoint="/api/gateway/v1/ping/"
    else
        health_endpoint="/api/v2/ping/"
    fi
    
    if ! curl -s -f -k "${AAP_URL}${health_endpoint}" >/dev/null 2>&1; then
        log_error "Existing AAP instance is not reachable"
        log_error "Health check failed: ${AAP_URL}${health_endpoint}"
        return 1
    fi
    
    log_success "Existing AAP instance is ready"
    return 0
}

# =============================================================================
# Diagnostics & Debugging
# =============================================================================

capture_diagnostics() {
    log_phase "Diagnostic Information"
    
    log_info "Capturing diagnostic data..."
    
    # Container status
    log_info "Container status:"
    $CONTAINER_RUNTIME ps -a 2>/dev/null | head -20 || log_warning "Failed to get container status"
    
    # Disk space
    log_info "Disk space:"
    df -h /tmp 2>/dev/null || log_warning "Failed to check /tmp space"
    df -h "$SCRIPT_DIR" 2>/dev/null || log_warning "Failed to check current directory space"
    
    # Port status
    log_info "Port status (44925, 44926):"
    ss -tuln 2>/dev/null | grep -E '44925|44926' || log_info "No processes on AAP ports"
    
    # Network connectivity
    log_info "Network connectivity:"
    # AAP_URL: unbound variable
    curl -s -o /dev/null -w "HTTP %{http_code}\n" -k "$AAP_URL/api/v2/ping/" 2>/dev/null || log_warning "Cannot reach AAP API"
}

provide_debugging_guidance() {
    log_phase "Debugging Guidance"
    
    log_info "Troubleshooting steps:"
    log_info ""
    log_info "1. Check container logs:"
    log_info "   $CONTAINER_RUNTIME ps -a"
    log_info "   $CONTAINER_RUNTIME logs <container-id>"
    log_info ""
    log_info "2. Check aap-dev status:"
    log_info "   cd $AAP_DEV_DIR"
    log_info "   make status"
    log_info ""
    log_info "3. Check disk space:"
    log_info "   df -h /tmp"
    log_info "   df -h ."
    log_info ""
    log_info "4. Review aap-dev documentation:"
    log_info "   https://github.com/ansible/aap-dev"
    log_info ""
    log_info "5. Run with verbose mode:"
    log_info "   bash -x ./setup_aap.sh"
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    local start_time=$(date +%s)
    
    echo ""
    echo "========================================"
    echo "AAP Instance Setup (Phase 1)"
    echo "========================================"
    echo ""
    
    # Parse arguments
    parse_arguments "$@"
    
    # Prerequisites check
    check_prerequisites || exit 1
    check_all_disk_space || exit 1
    
    # Skip AAP mode
    if [ "$SKIP_AAP" = true ]; then
        validate_existing_aap || exit 1
    else
        # Port check
        check_port || exit 1
        
        # Setup aap-dev repository
        setup_aap_dev_repo || exit 1
        
        # Start AAP
        start_aap || exit 1
        
        # Health check
        check_aap_health || exit 1
        
        # Retrieve credentials
        retrieve_admin_password || exit 1
        validate_admin_credentials || exit 1
        
        # Export configuration
        generate_aap_access_json || exit 1
    fi
    
    # Success summary
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    echo "========================================"
    echo "✅ AAP Setup Complete"
    echo "========================================"
    echo "AAP Version: $AAP_VERSION_ARG"
    echo "AAP URL: $AAP_URL"
    echo "Admin Username: $AAP_USERNAME"
    echo "Admin Password: \$AAP_PASSWORD (exported)"
    echo "Configuration: $AAP_ACCESS_JSON"
    echo "Duration: ${duration}s"
    echo "========================================"
    echo ""
    echo "Next steps:"
    echo "  1. Access AAP UI: xdg-open $AAP_URL"
    echo "  2. Test API: curl -k -u admin:\$AAP_PASSWORD $AAP_URL/api/v2/me/"
    echo "  3. Ready for Phase 2: ./setup_aap_data.sh (coming soon)"
    echo ""
}

# Run main function
main "$@"
