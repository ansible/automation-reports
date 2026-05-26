# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Automation Dashboard — a reporting and analytics platform for Ansible Automation Platform (AAP) deployments. Full-stack monorepo: Django 5.2 backend + React 19 frontend + dispatcherd task system. Data is pulled from AAP clusters via OAuth2 and surfaced as charts, tables, and exportable reports.

---

## Dev Environment Setup

**Always source `.env.sh` first** — it activates the venv, loads `.env`, and sets `PYTHONPATH=src/`.

```bash
source .env.sh
```

Required services (5 terminals):

```bash
# 1. Database + Redis
(cd compose; docker compose --project-directory .. -f compose.yml up --build db redis)

# 2. Migrations + initial data (once)
cd src/backend
python manage.py migrate
python manage.py createsuperuser
python manage.py setclusters ../clusters.yaml

# 3. Django dev server  →  http://localhost:8000
python manage.py runserver

# 4. Task dispatcher (required for sync jobs to actually run)
python manage.py run_dispatcher

# 5. Frontend dev server  →  http://localhost:9000
nvm use v22.21.1
cd src/frontend && npm install && npm run start:dev
```

Frontend queries the backend at `http://localhost:8000/api/v1/*` — backend must be up first. Sync tasks queue immediately but won't process unless the dispatcher is running.

---

## Commands

### Backend

```bash
# Tests (run from src/backend)
pytest --cov=backend
pytest tests/unit/test_parser.py                         # single file
pytest tests/unit/test_parser.py::test_something         # single test

# Backend tests need CREATEDB permission on the DB user
# docker exec -it aapdashboard-db-1 psql -c 'ALTER USER root CREATEDB;'

# Sync AAP data manually
python manage.py syncdata --since=2025-02-12 --until=2025-02-12

# Requirements (source of truth is requirements-pinned.txt)
make sync-requirements    # regenerate requirements-build.txt
make requirements-check   # verify in sync
make sync-build-tools     # regenerate requirements-build-tools.txt (run after sync-requirements)
```

### Frontend

```bash
# From src/frontend
npm run type-check    # TypeScript
npm run eslint        # lint
npm run format        # Prettier
npm run build         # production bundle

# E2E tests (Playwright)
npx playwright install chromium   # one-time
npx playwright test               # headless
npx playwright test --headed      # with browser UI
npx playwright test --debug       # debug mode
```

---

## Architecture

### Data Flow

```
AAP Cluster (OAuth2)
      │
      ▼
dispatcherd workers
      │  fetch incremental job data
      ▼
ClusterSyncData (raw JSON in DB)
      │
      ▼  DB trigger fires
data parser
      │  normalises into structured models
      ▼
Job / JobHostSummary / Host tables
      │
      ▼
DRF API  ←──  React SPA (charts, tables, exports)
```

### Key Architectural Points

**dispatcherd replaces Celery/dramatiq.** Background tasks (sync, parse, schedule management) go through `apps/dispatch/` and are triggered via PostgreSQL `pg_notify`. The dispatcher must be running as a separate process — it is not embedded in the Django server.

**Two-phase data ingestion.** Raw API responses are stored first in `ClusterSyncData`; a DB trigger then fires the parser to convert them into normalised models. This decouples network I/O from data transformation and allows re-parsing without re-fetching.

**OAuth2 per cluster.** Each AAP cluster has its own OAuth2 credentials stored in the database (loaded via `setclusters`). The `apps/aap_auth/` app handles token refresh. Local OAuth2 config goes in `src/backend/django_config/local_settings.py` (copy from `local_settings.example.py`).

**Frontend is a pure SPA.** There are no server-rendered pages outside Django admin. All data comes from `/api/v1/` endpoints. The Vite dev server proxies to the Django backend; in production, nginx serves the built assets and proxies API calls.

**Settings layering.** `django_config/settings.py` is the base; `local_settings.py` (gitignored) overrides for local dev (OAuth2, SSO). Tests use `backend/tests/settings_for_test.py` — no migrations are run (`--nomigrations`), keeping the test suite fast.

### Directory Map (non-obvious parts)

| Path | Purpose |
|------|---------|
| `src/backend/apps/clusters/` | Cluster models + OAuth2 sync orchestration |
| `src/backend/apps/scheduler/` | Cron-like sync schedule management |
| `src/backend/apps/dispatch/` | dispatcherd integration (task definitions, queue) |
| `src/backend/apps/tasks/` | Concrete background task implementations |
| `src/backend/apps/aap_auth/` | OAuth2 token lifecycle per cluster |
| `src/backend/analytics/` | Aggregation/reporting logic (not Django apps) |
| `src/backend/api/v1/` | All DRF viewsets and routers |
| `src/backend/tests/mock_aap/` | Pre-recorded AAP API responses for unit tests |
| `src/frontend/app/Services/` | Axios-based API client layer |
| `src/frontend/app/Store/` | Redux Toolkit + Zustand state |
| `src/frontend/app/Components/Charts/` | Victory chart wrappers |
| `docs/` | Architecture deep-dives (sync, schema, security, etc.) |

### Key Dependencies

**Backend:** Django 5.2, DRF, dispatcherd, psycopg 3, drf-spectacular (OpenAPI), django-filters, django-solo (singleton settings model), Pydantic 2.

**Frontend:** React 19, PatternFly 6 (UI kit), Victory 37 (charts), React Router 7, Axios, Redux Toolkit, Zustand.

**Node version:** 22.21.1 (use `nvm use`). **Python version:** 3.12.
