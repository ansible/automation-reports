#!/bin/bash

# sync-requirements.sh
# Script to automatically sync requirements-pinned.txt and requirements-build.txt from requirements.txt

set -e

echo "Syncing requirements files from requirements.txt..."

# Generate pinned requirements with security hashes
echo "Generating requirements-pinned.txt..."
pip-compile --generate-hashes --output-file=requirements-pinned.txt requirements.txt

# Generate build requirements from pinned requirements
echo "Generating requirements-build.txt..."
pip-compile --generate-hashes --output-file=requirements-build.txt requirements-pinned.txt

echo "Requirements files synced successfully!"
