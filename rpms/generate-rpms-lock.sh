#!/bin/bash

# Generate rpms.lock.yaml from rpms.in.yaml using public UBI images only.
# Uses registry.access.redhat.com so the lock can be generated without
# registry.redhat.io authentication.
#
# USAGE: Run from project root: ./rpms/generate-rpms-lock.sh
#
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_debug() { echo -e "${BLUE}[DEBUG]${NC} $1"; }
log_and_exec() { log_debug "Executing: $1" >&2; eval "$1"; }

log_info "=== RPM Lock-YAML Generator (public images only) ==="

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ ! -f "rpms.in.yaml" ]]; then
    log_error "rpms.in.yaml not found in project root: $PROJECT_ROOT"
    exit 1
fi
log_info "Found rpms.in.yaml"

# Always use public UBI image so lock generation works without registry.redhat.io auth
PUBLIC_IMAGE="registry.access.redhat.com/ubi9/ubi-minimal:latest"
log_info "Using base image: $PUBLIC_IMAGE"

# Build rpm-lockfile container (uses public UBI)
log_info "Building rpm-lockfile-prototype container..."
cd rpms/rpm-lockfile-container
log_and_exec "podman build -t rpm-lockfile-prototype:latest ."
cd "$PROJECT_ROOT"

# Run with public image
log_info "Running rpm-lockfile-prototype..."
log_and_exec "podman run \
  -e GIT_SSL_NO_VERIFY=true \
  --security-opt label=disable \
  -v $PWD:/data \
  rpm-lockfile-prototype:latest \
  --image $PUBLIC_IMAGE \
  /data/rpms.in.yaml \
  --outfile /data/rpms.lock.yaml"

log_info "✓ RPM lockfile generation complete!"
log_info "Output written to: rpms.lock.yaml"
log_info "All images/repos used are public (registry.access.redhat.com, cdn-ubi.redhat.com)."
