#!/bin/bash

# sync-requirements.sh
# Script to automatically sync requirements-build.txt from requirements-pinned.txt

set -e

trap '
    echo "An error occurred. Reverting changes in requirements-pinned.txt and exiting..."
    git checkout requirements-pinned.txt
    exit 1
' ERR

# Check if requirements-pinned.txt has local modifications
if ! git diff --quiet requirements-pinned.txt || ! git diff --cached --quiet requirements-pinned.txt; then
    echo "Error: requirements-pinned.txt has local modifications. Please commit or discard changes first."
    exit 1
fi

echo "Syncing requirements files from requirements-pinned.txt..."

# Append each command line argument to requirements-pinned.txt
for arg in "$@"; do
    echo "$arg" >> requirements-pinned.txt
done
# Generate build requirements from pinned requirements
echo "Generating requirements-build.txt..."
pip-compile --generate-hashes --output-file=requirements-build.txt requirements-pinned.txt
git checkout requirements-pinned.txt

echo "Requirements files synced successfully!"
