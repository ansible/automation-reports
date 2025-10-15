#!/bin/bash

# sync-requirements.sh
# Script to automatically sync requirements-build.txt from requirements-pinned.txt

set -e

echo "Syncing requirements files from requirements-pinned.txt..."

# Generate build requirements from pinned requirements
echo "Generating requirements-build.txt..."
pip-compile --no-header --generate-hashes --output-file=requirements-build.txt requirements-pinned.txt

echo "Requirements files synced successfully!"
