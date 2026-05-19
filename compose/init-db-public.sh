#!/bin/bash
# Grants CREATEDB to the app user — for postgres:15 (public image).
# Runs automatically via /docker-entrypoint-initdb.d/ on first start.
set -e
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
    ALTER USER "$POSTGRES_USER" CREATEDB;
EOSQL
