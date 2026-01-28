#!/usr/bin/env bash
#
# cleanup_aap.sh - Stop AAP instance and free resources
#
# Usage: ./cleanup_aap.sh [OPTIONS]
#
# Options:
#   --version VERSION      Clean specific AAP version (optional, cleans all if not specified)
#   --remove-aap-dev       Remove aap-dev directory
#   --force                Skip confirmation prompts
#
# Phase 1 of 4: AAP Instance cleanup

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AAP_DEV_DIR="${SCRIPT_DIR}/aap-dev"
AAP_ACCESS_JSON="${SCRIPT_DIR}/aap_access.json"

# Options
VERSION_ARG=""
REMOVE_AAP_DEV=false
FORCE=false

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
            --version)
                VERSION_ARG="$2"
                shift 2
                ;;
            --remove-aap-dev)
                REMOVE_AAP_DEV=true
                shift
                ;;
            --force)
                FORCE=true
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

    # Validate version if specified
    if [[ -n "$VERSION_ARG" && ! "$VERSION_ARG" =~ ^(2\.5|2\.6)$ ]]; then
        log_error "Invalid AAP version: $VERSION_ARG (must be 2.5 or 2.6)"
        exit 1
    fi
}

show_usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Stop AAP instance and free resources.

OPTIONS:
    --version VERSION      Clean specific AAP version (optional, cleans all if not specified)
    --remove-aap-dev       Remove aap-dev directory
    --force                Skip confirmation prompts
    -h, --help             Show this help message

EXAMPLES:
    # Stop AAP with confirmation
    ./cleanup_aap.sh

    # Stop AAP without confirmation
    ./cleanup_aap.sh --force

    # Stop and remove aap-dev directory
    ./cleanup_aap.sh --remove-aap-dev --force

    # Clean specific version
    ./cleanup_aap.sh --version 2.6 --force

EOF
}

# =============================================================================
# Cleanup Confirmation
# =============================================================================

show_cleanup_plan() {
    log_phase "Cleanup Plan"
    
    echo "The following actions will be performed:"
    echo ""
    
    # AAP instance
    if [ -n "$VERSION_ARG" ]; then
        echo "  - Stop AAP $VERSION_ARG instance"
    else
        echo "  - Stop all AAP instances"
    fi
    
    # Port status
    if [ -n "$VERSION_ARG" ]; then
        if [[ "$VERSION_ARG" == "2.5" ]]; then
            echo "  - Free port 44925"
        else
            echo "  - Free port 44926"
        fi
    else
        echo "  - Free ports 44925 and 44926"
    fi
    
    # Configuration file
    if [ -f "$AAP_ACCESS_JSON" ]; then
        echo "  - Remove aap_access.json"
    fi
    
    # aap-dev directory
    if [ "$REMOVE_AAP_DEV" = true ] && [ -d "$AAP_DEV_DIR" ]; then
        echo "  - Remove aap-dev directory (~500MB)"
    fi
    
    echo ""
}

confirm_cleanup() {
    if [ "$FORCE" = true ]; then
        log_info "Force mode enabled, skipping confirmation"
        return 0
    fi
    
    show_cleanup_plan
    
    read -p "Proceed with cleanup? (yes/no): " -r response
    echo ""
    
    case "$response" in
        yes|y|Y|YES)
            return 0
            ;;
        *)
            log_info "Cleanup cancelled by user"
            exit 0
            ;;
    esac
}

# =============================================================================
# AAP Shutdown
# =============================================================================

stop_aap() {
    log_phase "AAP Instance Shutdown"
    
    if [ ! -d "$AAP_DEV_DIR" ]; then
        log_warning "aap-dev directory not found: $AAP_DEV_DIR"
        log_warning "No AAP instance to stop"
        return 0
    fi
    
    cd "$AAP_DEV_DIR"
    
    log_info "Stopping AAP instance using make clean..."
    log_info "This will remove the kind cluster and all AAP containers"
    
    # Run make clean to remove kind cluster
    if make clean 2>&1 | tee /tmp/cleanup_aap.log; then
        log_success "AAP instance stopped successfully"
    else
        log_error "Failed to stop AAP instance"
        log_error "Check logs: /tmp/cleanup_aap.log"
        return 1
    fi
    
    return 0
}

# =============================================================================
# File Cleanup
# =============================================================================

cleanup_aap_access_json() {
    if [ -f "$AAP_ACCESS_JSON" ]; then
        log_info "Removing aap_access.json..."
        rm -f "$AAP_ACCESS_JSON"
        log_success "Removed: $AAP_ACCESS_JSON"
    else
        log_info "No aap_access.json to remove"
    fi
}

cleanup_aap_dev_directory() {
    if [ "$REMOVE_AAP_DEV" = false ]; then
        log_info "Keeping aap-dev directory (use --remove-aap-dev to remove)"
        return 0
    fi
    
    if [ ! -d "$AAP_DEV_DIR" ]; then
        log_info "No aap-dev directory to remove"
        return 0
    fi
    
    log_info "Removing aap-dev directory..."
    log_info "This will remove ~500MB of data"
    
    rm -rf "$AAP_DEV_DIR"
    
    if [ -d "$AAP_DEV_DIR" ]; then
        log_error "Failed to remove aap-dev directory"
        return 1
    fi
    
    log_success "Removed: $AAP_DEV_DIR"
    return 0
}

# =============================================================================
# Port Verification
# =============================================================================

verify_ports_freed() {
    log_phase "Port Verification"
    
    local ports_to_check=()
    
    if [ -n "$VERSION_ARG" ]; then
        if [[ "$VERSION_ARG" == "2.5" ]]; then
            ports_to_check=(44925)
        else
            ports_to_check=(44926)
        fi
    else
        ports_to_check=(44925 44926)
    fi
    
    local ports_still_in_use=()
    
    for port in "${ports_to_check[@]}"; do
        if ss -tuln 2>/dev/null | grep -q ":${port} " || netstat -tuln 2>/dev/null | grep -q ":${port} "; then
            ports_still_in_use+=("$port")
        else
            log_info "Port $port is free"
        fi
    done
    
    if [ ${#ports_still_in_use[@]} -gt 0 ]; then
        log_warning "Ports still in use: ${ports_still_in_use[*]}"
        log_warning "These may be in TIME_WAIT state or used by other processes"
        log_info ""
        log_info "Check with:"
        for port in "${ports_still_in_use[@]}"; do
            log_info "  sudo lsof -i :$port"
        done
        return 0
    fi
    
    log_success "All AAP ports freed"
    return 0
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    echo ""
    echo "========================================"
    echo "AAP Instance Cleanup (Phase 1)"
    echo "========================================"
    echo ""
    
    # Parse arguments
    parse_arguments "$@"
    
    # Confirm cleanup
    confirm_cleanup
    
    # Stop AAP
    stop_aap || {
        log_error "Failed to stop AAP instance"
        exit 1
    }
    
    # Cleanup files
    log_phase "File Cleanup"
    cleanup_aap_access_json
    cleanup_aap_dev_directory
    log_success "File cleanup complete"
    
    # Verify ports freed
    verify_ports_freed
    
    # Success summary
    echo ""
    echo "========================================"
    echo "✅ AAP Cleanup Complete"
    echo "========================================"
    
    if [ -n "$VERSION_ARG" ]; then
        echo "Cleaned AAP version: $VERSION_ARG"
    else
        echo "Cleaned all AAP instances"
    fi
    
    if [ "$REMOVE_AAP_DEV" = true ]; then
        echo "Removed aap-dev directory"
    else
        echo "Kept aap-dev directory (use --remove-aap-dev to remove)"
    fi
    
    echo "========================================"
    echo ""
    echo "To start AAP again:"
    echo "  ./setup_aap.sh"
    echo ""
}

# Run main function
main "$@"
