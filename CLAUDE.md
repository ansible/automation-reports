# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**automation-reports** is a monorepo dashboard for Ansible Automation Platform (AAP). It syncs job data from one or more AAP clusters via OAuth2, stores it in PostgreSQL, and serves analytics/reporting through a REST API and React frontend.

Stack: Django 5 + DRF (backend), React 19 + TypeScript + PatternFly (frontend), dispatcherd (background tasks), PostgreSQL, Redis.

---

## Environment Setup

```bash
# Python
python3.12 -m venv .venv
cp .env.example .env          # fill in DB credentials and secrets
source .env.sh                # loads .env + activates venv + sets PYTHONPATH=$PWD/src

# Node
nvm use v22.21.1
cd src/frontend && npm install
```

Local Django overrides go in `src/backend/django_config/local_settings.py` (copy from `local_settings.example.py`).

Cluster connection config (OAuth2 tokens, addresses, sync schedules) goes in `clusters.yaml` (copy from `clusters.example.yaml`).

---

## Development Commands

### Backend

```bash
# From repo root, after `source .env.sh`
cd src/backend
python manage.py migrate
python manage.py setclusters clusters.yaml   # load cluster config
python manage.py getclusters                 # export cluster config (encrypted)
python manage.py runserver                   # API on :8000
python manage.py run_dispatcher              # background task processor (separate terminal)
python manage.py syncdata --since=DATE --until=DATE  # manual sync
```

### Frontend

```bash
cd src/frontend
npm run start:dev    # Vite dev server on :9000 (proxies API to :8000)
npm run build        # tsc check + Vite production build
npm run lint         # ESLint
npm run format       # Prettier check
npm run type-check   # TypeScript only
npm run ci-checks    # type-check + lint + test:coverage (canonical CI gate)
```

### Docker (for DB + Redis only in dev)

```bash
docker compose -f compose/compose.yml up db redis
```

### Dependency Management

```bash
make sync-requirements    # recompile and pin requirements-build.txt via pip-compile
make requirements-check   # verify requirements-build.txt is in sync (used in CI)
```

---

## Testing

### Backend

```bash
# From repo root, after `source .env.sh`
pytest                          # all tests (creates a fresh DB each run via --create-db)
pytest tests/path/to/test.py    # single file
pytest --cov=backend            # with coverage
```

Config in `pyproject.toml` (`[tool.pytest.ini_options]`). Test settings: `src/backend/tests/settings_for_test.py`. Migrations are disabled in tests (`--nomigrations`). Pre-recorded AAP HTTP responses for mocking live in `src/backend/tests/mock_aap/`.

### Frontend (Playwright E2E)

```bash
npx playwright install chromium   # first time
npx playwright test               # headless
npx playwright test --headed      # show browser
```

Tests live in `tests/playwright/specs/`. Config: `playwright.config.ts`. Requires dev server running on `:9000`. On CI, workers=1 with 2 retries; locally fully parallel.

---

## Architecture

### Backend (`src/backend/`)

Django apps in `src/backend/apps/`:

| App | Purpose |
|-----|---------|
| `clusters` | Core: AAP cluster models, data sync connector, job/event parsing |
| `aap_auth` | OAuth2 authentication against AAP |
| `dispatch` | dispatcherd integration for background tasks |
| `scheduler` | RFC 5545 rrule-based sync scheduling |
| `tasks` | Background task definitions |
| `analytics` | Prometheus metrics collectors and aggregation pipeline |
| `common` | Shared utilities and base models |
| `users` | User management |

Key files:
- `apps/clusters/connector.py` (~17k lines) — AAP API client: OAuth2, data fetch, credential management
- `apps/clusters/parser.py` (~14k lines) — job event parsing and metrics calculation
- `apps/clusters/models.py` — core domain models: `Cluster`, `Job`, `JobTemplate`, `Organization`, `SubscriptionCost` (singleton via django-solo)
- `analytics/metrics.py` — Prometheus gauge definitions (jobs total, by status, by type); exposed at `/api/v1/metrics/`
- `django_config/settings.py` — split settings via `split-settings` library
- `api/v1/` — DRF viewsets and routers; OpenAPI schema at `/api/v1/schema/`

Settings split: base settings + optional `local_settings.py`. Key env-configurable vars: `JOB_EVENT_WORKERS` (default 4), `SCHEDULE_MAX_DATA_PARSE_JOBS` (default 30).

Request tracing: `django_guid` middleware injects a request ID into every response.

### Frontend (`src/frontend/app/`)

Built with **Vite** (not webpack). PatternFly 6 + Victory charts.

| Directory | Purpose |
|-----------|---------|
| `AppLayout/` | Shell layout components |
| `Components/` | Reusable UI components (tables, filters, date picker, etc.) |
| `Dashboard/` | Main dashboard page with bar charts and totals |
| `Store/` | Zustand stores: `authStore`, `filterStore`, `filterOptionsStore`, `commonStore` |
| `Services/` | API calls via `RestService.ts` |
| `client/` | Axios instance + request interceptors |
| `Types/` | TypeScript interfaces |
| `Utils/` | Shared helpers |

Routing via React Router 7. Auth flow: `/login` → OAuth2 to AAP → `/auth-callback` → token stored in `authStore`.

### Task Processing

Background tasks use **dispatcherd** (replaces Celery/dramatiq). The dispatcher process (`python manage.py run_dispatcher`) must be running for sync jobs to execute. Sync jobs are enqueued by the scheduler based on rrule schedules defined in `clusters.yaml`.

### Data Flow

```
AAP Cluster API
  └─► connector.py (OAuth2 fetch)
      └─► parser.py (event/metrics parsing)
          └─► PostgreSQL models (clusters app)
              └─► DRF API (api/v1/)
                  └─► React frontend
```

### Container Layout

The production image (multi-stage `Dockerfile.backend`) runs nginx on port **8053**, serving the Vite-built frontend as static files and proxying `/api/` to uvicorn (ASGI). Development uses separate :8000 (Django) and :9000 (Vite) processes.

---

## Key Conventions

- **Python path**: `PYTHONPATH=$PWD/src` (set by `.env.sh`); import as `from backend.apps...` or `from apps...`
- **Prettier**: single quotes, 120 char print width
- **ESLint**: TypeScript strict, `sort-imports` enforced, PropTypes disabled (use TS types)
- **API versioning**: all endpoints under `/api/v1/`; pagination default 100 items
- **Cluster secrets** (tokens, credentials) are encrypted at rest; use `getclusters` management command to export with encryption
- **Pinned deps**: `requirements-build.txt` is the pinned lockfile; edit `requirements.txt` then run `make sync-requirements` to regenerate it
