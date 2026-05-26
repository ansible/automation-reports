#!/bin/bash
# Generate requirements-build-tools.txt using pybuild-deps.
#
# Run this whenever requirements-build.txt changes to refresh the set of
# build backends pre-fetched by Cachi2 in the hermetic Konflux build.
#
# USAGE: run from the project root:
#   ./requirements/generate-build-requirements.sh
#
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ ! -f "requirements-build.txt" ]]; then
    echo "ERROR: requirements-build.txt not found in $PROJECT_ROOT" >&2
    exit 1
fi

echo "[INFO] Building pybuild-deps container..."
cd requirements/pybuild-deps-container
podman build -t pybuild-deps .
cd "$PROJECT_ROOT"

echo "[INFO] Generating requirements-build-tools.txt from requirements-build.txt..."
podman run --rm \
    -v "$PROJECT_ROOT:/data" \
    pybuild-deps \
    pybuild-deps compile --generate-hashes \
        --output-file=requirements-build-tools.txt \
        requirements-build.txt

echo "[INFO] Done. requirements-build-tools.txt updated ($(wc -l < requirements-build-tools.txt) lines)."
