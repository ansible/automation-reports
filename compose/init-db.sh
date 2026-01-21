#!/bin/bash
# Grant CREATEDB permission to the database user
# This script runs on container startup inside the PostgreSQL container

set -e

echo "Granting CREATEDB permission to ${POSTGRESQL_USER}..."

# Run as postgres superuser without password (local socket connection)
psql -v ON_ERROR_STOP=1 -U postgres -d postgres <<-EOSQL
    ALTER USER "${POSTGRESQL_USER}" CREATEDB;
EOSQL

echo "CREATEDB permission granted to ${POSTGRESQL_USER}"
