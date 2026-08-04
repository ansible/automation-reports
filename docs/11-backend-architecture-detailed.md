# Backend Architecture — Detailed

## Overview

The backend is a **Django 5.2** application with **Django REST Framework 3.16**. It ingests automation job data from AAP clusters on a scheduled basis, stores it in PostgreSQL, and exposes aggregated metrics via a REST API. Background work runs through **dispatcherd** (a pg_notify-based task system that replaced Celery). Authentication is delegated to AAP's OAuth2 provider; the backend issues short-lived JWT cookies for session management.

---

## High-Level System Architecture

```mermaid
graph TB
    subgraph "External"
        AAP["AAP Cluster\n(Controller API)"]
        Browser["Browser (SPA)"]
    end

    subgraph "automation-reports"
        Nginx["nginx\n(reverse proxy)"]
        UWSGI["uWSGI\n(WSGI server)"]
        Django["Django App\n(DRF API)"]
        Dispatcher["dispatcherd\n(background worker)"]
        PG["PostgreSQL\n(data + advisory locks + pg_notify)"]
        Redis["Redis\n(Django Channels layer)"]
    end

    Browser -->|"HTTPS :8053"| Nginx
    Nginx -->|"static files"| Browser
    Nginx -->|"/api/ proxy"| UWSGI
    UWSGI --> Django
    Django --> PG
    Django --> Redis
    Dispatcher -->|"pg_notify listener"| PG
    Dispatcher -->|"AAP REST API"| AAP
    Dispatcher -->|"writes Job/Template/Org data"| PG
```

Both the Django API server (uWSGI) and the dispatcher are started by **supervisord** inside the container. The dispatcher runs as a separate OS process: `python manage.py run_dispatcher`.

---

## Django Application Structure

```mermaid
graph TD
    subgraph "django_config (project)"
        Settings["settings.py\n+ local_settings.py\n+ /etc/dashboard/conf.d/*.py"]
        URLs["urls.py\n(root URL config)"]
        WSGI["wsgi.py"]
        ASGI["asgi.py"]
    end

    subgraph "Installed Apps"
        clusters["apps.clusters\n(core data models + sync)"]
        scheduler["apps.scheduler\n(RRULE schedule + SyncJob queue)"]
        dispatch["apps.dispatch\n(dispatcherd integration)"]
        tasks["apps.tasks\n(concrete task implementations)"]
        aap_auth["apps.aap_auth\n(OAuth2 + JWT lifecycle)"]
        common["apps.common\n(Currency, Settings, FilterSet)"]
        users["apps.users\n(User model)"]
        analytics["analytics\n(Prometheus metrics)"]
    end

    URLs --> clusters
    URLs --> scheduler
    URLs --> aap_auth
    URLs --> common
    URLs --> users
    URLs --> analytics
    dispatch --> tasks
    tasks --> clusters
    tasks --> scheduler
```

---

## Django Apps — Detailed

### `apps.clusters` — Core Data Layer

```mermaid
graph LR
    subgraph "models"
        Cluster
        ClusterSyncData["ClusterSyncData\n(raw JSON from AAP)"]
        ClusterSyncStatus["ClusterSyncStatus\n(last sync timestamp)"]
        Organization
        JobTemplate["JobTemplate\n(cost parameters)"]
        Job["Job\n(status, elapsed, host counts)"]
        JobLabel["JobLabel\n(M2M: Job ↔ Label)"]
        JobHostSummary
        Host
        Inventory
        ExecutionEnvironment
        InstanceGroup
        Label
        Project
        AAPUser
        SubscriptionCost["SubscriptionCost\n(singleton: monthly cost + rate)"]
        DateRangeChoices["DateRangeChoices\n(enum: preset date ranges)"]
    end

    subgraph "logic"
        connector["connector.py\n(AAPConnector: REST calls to AAP)"]
        parser["parser.py\n(ClusterDataParser: raw→models)"]
        encryption["encryption.py\n(AES-256 for cluster creds)"]
        schemas["schemas.py\n(Pydantic shapes for AAP API)"]
    end

    ClusterSyncData -->|"save() auto-creates"| SyncJob["SyncJob(PARSE_JOB_DATA)"]
    connector -->|"fetches from AAP"| ClusterSyncData
    parser -->|"reads"| ClusterSyncData
    parser -->|"writes"| Job
    parser -->|"writes"| JobTemplate
    parser -->|"writes"| Organization
    Cluster -->|"AES-encrypted tokens"| encryption
```

`ClusterSyncData.save()` automatically creates a `SyncJob` of type `PARSE_JOB_DATA` when raw data arrives, ensuring the parse pipeline always runs after a sync.

### `apps.scheduler` — Sync Schedule

```mermaid
graph LR
    SyncSchedule["SyncSchedule\n(RFC 5545 RRULE)\n- cluster FK\n- rrule string\n- last_run timestamp"]
    SyncScheduleState["SyncScheduleState\n(singleton: is_paused)"]
    SyncJob["SyncJob\n- cluster FK\n- job_type (SYNC_DATA / PARSE_JOB_DATA)\n- status (PENDING / RUNNING / COMPLETE / FAILED)\n- created_at"]

    SyncSchedule -->|"due entries create"| SyncJob
    SyncScheduleState -->|"pauses"| SyncSchedule
```

The scheduler fires sync jobs based on RRULE expressions. The periodic task `automation_dashboard_periodic_scheduler` runs every 20 seconds and checks for due schedules using a **PostgreSQL advisory lock** to prevent double-execution across dispatcher instances.

### `apps.dispatch` — Dispatcherd Integration

```mermaid
graph LR
    DashboardTaskWorker["DashboardTaskWorker\n(subclass of dispatcherd TaskWorker)"]
    RunDispatcher["manage.py run_dispatcher"]
    PGNotify["pg_notify channels:\n- automation_dashboard_sync_channel\n- automation_dashboard_parse_channel\n- automation_dashboard_metrics_channel"]
    hazmat["hazmat.py\n(startup/shutdown hooks)"]

    RunDispatcher --> DashboardTaskWorker
    DashboardTaskWorker --> PGNotify
    DashboardTaskWorker --> hazmat
```

`dispatcherd` replaced Celery. Tasks are triggered by PostgreSQL `pg_notify` messages on named channels. Advisory locks prevent concurrent execution of the same task type.

### `apps.tasks` — Task Implementations

```mermaid
graph LR
    AAPSyncTask["AAPSyncTask\n(jobs.py)\nFetches from AAP REST API:\n- organizations\n- job templates\n- jobs\nWrites to ClusterSyncData"]
    AAPParseDataTask["AAPParseDataTask\n(jobs.py)\nReads ClusterSyncData\nWrites Job, JobTemplate, etc.\nDeletes raw record on success"]
    PeriodicScheduler["automation_dashboard_periodic_scheduler\n(system.py)\nEvery 20s: check SyncSchedule, fire sync jobs"]
    ParseScheduler["automation_dashboard_job_parser_data_scheduler\n(system.py)\nEvery 5s: pick up PENDING PARSE_JOB_DATA SyncJobs"]
    SyncTaskManager["sync_task_manager\n(system.py)\nEvery 20s: SyncTaskManager.schedule()"]
    MetricsTask["send_subsystem_metrics\n(analytics_tasks.py)\nEvery 20s: push Prometheus metrics"]

    PeriodicScheduler -->|"pg_notify sync channel"| AAPSyncTask
    ParseScheduler -->|"pg_notify parse channel"| AAPParseDataTask
    SyncTaskManager --> PeriodicScheduler
```

---

## Auth Architecture

```mermaid
sequenceDiagram
    participant Browser
    participant Django as Django (AAPAuthentication DRF class)
    participant AAPAuth as AAPAuth (apps/aap_auth/aap_auth.py)
    participant AAP as AAP OAuth2 server
    participant DB as PostgreSQL (JwtUserToken)

    Browser->>Django: POST /api/v1/aap_auth/token/ {auth_code, redirect_uri}
    Django->>AAPAuth: exchange_code(auth_code, redirect_uri)
    AAPAuth->>AAP: POST /o/token/ (authorization_code grant)
    AAP-->>AAPAuth: {access_token, refresh_token}
    AAPAuth->>AAP: GET /api/gateway/v1/me/ (using AAP access_token)
    AAP-->>AAPAuth: {username, email, is_superuser, ...}
    AAPAuth->>DB: create_or_update_aap_user(user_data)
    AAPAuth->>DB: JwtUserToken.create(user, access_token, refresh_token)
    Django-->>Browser: Set-Cookie: access_token (60s, HttpOnly, SameSite=Lax)\nSet-Cookie: refresh_token (24h, HttpOnly, SameSite=Lax)

    Note over Browser,Django: Subsequent requests
    Browser->>Django: GET /api/v1/report/ (access_token cookie)
    Django->>Django: AAPAuthentication.authenticate(request)
    Django->>Django: JWTToken.decode_token(access_token cookie)
    Django->>DB: validate token not revoked
    Django-->>Browser: 200 OK

    Note over Browser,Django: Token expiry
    Browser->>Django: POST /api/v1/aap_auth/refresh_token/ (refresh_token cookie)
    Django->>DB: JwtUserRefreshToken.rotate(refresh_token)
    Django-->>Browser: Set-Cookie: new access_token (60s)\nSet-Cookie: new refresh_token (24h)
```

Key implementation details:
- `AAPAuthentication` (DRF `BaseAuthentication` subclass) validates the JWT from the `access_token` cookie on every request
- CSRF enforcement is applied to all state-mutating requests
- `is_platform_auditor` field on `User` grants admin-equivalent API access without Django `is_staff`
- All cluster credentials (tokens for connecting to AAP clusters) are stored AES-256-encrypted in the DB

---

## Data Sync Pipeline

```mermaid
flowchart TD
    Schedule["SyncSchedule (RRULE)\ndue check every 20s"]
    AdvisoryLock1["PostgreSQL Advisory Lock\n(prevent double-dispatch)"]
    CreateSyncJob["Create SyncJob\n(SYNC_DATA, PENDING)"]
    Notify1["pg_notify\nautomation_dashboard_sync_channel"]
    AAPSyncTask["AAPSyncTask\nGET /api/v2/organizations/\nGET /api/v2/job_templates/\nGET /api/v2/jobs/?since=..."]
    ClusterSyncData["ClusterSyncData.save()\n(raw JSON blob)"]
    AutoCreateJob["auto-creates SyncJob\n(PARSE_JOB_DATA, PENDING)"]
    Notify2["pg_notify\nautomation_dashboard_parse_channel"]
    AdvisoryLock2["PostgreSQL Advisory Lock\n(prevent double-parse)"]
    ParseTask["AAPParseDataTask\nClusterDataParser.parse()"]
    Models["Write:\nJob, JobHostSummary\nJobTemplate, Organization\nAAPUser, Project, etc."]
    Cleanup["Delete ClusterSyncData\n(raw record removed on success)"]

    Schedule --> AdvisoryLock1
    AdvisoryLock1 --> CreateSyncJob
    CreateSyncJob --> Notify1
    Notify1 --> AAPSyncTask
    AAPSyncTask --> ClusterSyncData
    ClusterSyncData --> AutoCreateJob
    AutoCreateJob --> Notify2
    Notify2 --> AdvisoryLock2
    AdvisoryLock2 --> ParseTask
    ParseTask --> Models
    ParseTask --> Cleanup
```

The sync pipeline is designed to be fault-tolerant: raw data (`ClusterSyncData`) is kept until parsing succeeds. If parsing fails, the record remains and can be retried. PostgreSQL advisory locks guarantee that each sync and each parse step runs exactly once even when multiple dispatcher processes are running.

---

## API Layer

### URL Structure

```mermaid
graph TD
    Root["/api/v1/"]
    Root --> ping["ping/ — health check"]
    Root --> template_options["template_options/ — bootstrap data"]
    Root --> report["report/ — main aggregated report"]
    Root --> costs["costs/ — SubscriptionCost update"]
    Root --> templates["templates/ — JobTemplate list + cost params"]
    Root --> common["common/ — Currency, Settings, FilterSet CRUD"]
    Root --> aap_auth["aap_auth/ — OAuth2 + JWT endpoints"]
    Root --> users["users/ — /me/"]
    Root --> labels["labels/ — Label list"]
    Root --> projects["projects/ — Project list"]
    Root --> orgs["organizations/ — Org list"]
    Root --> metrics["metrics/ — Prometheus exposition"]
    Root --> schema["schema/, docs/, redoc/ — OpenAPI"]

    aap_auth --> auth_settings["settings/ — authorize URL, client_id"]
    aap_auth --> auth_token["token/ — exchange OAuth code → JWT cookies"]
    aap_auth --> auth_refresh["refresh_token/ — rotate JWT cookies"]
    aap_auth --> auth_logout["logout/ — clear JWT cookies"]

    report --> report_list["GET list — paginated job template aggregates"]
    report --> report_details["GET details — totals + chart data + top users/projects"]
    report --> report_csv["GET csv — CSV download"]
    report --> report_pdf["POST pdf — WeasyPrint PDF with SVG charts"]
```

### Report View (`api/v1/report/views.py`) — Key Logic

```mermaid
flowchart TD
    Request["GET /api/v1/report/details/\n?date_range=last_30_days\n&organization=1,2\n&job_template=5"]
    Auth["AAPAuthentication + IsAuthenticated + IsAdmin"]
    Filters["Apply filters:\n- DateRangeChoices.get_date_range()\n- org, template, project, label IN clauses"]
    Aggregate["QuerySet aggregate:\n- COUNT(job.id) → total_runs\n- SUM(elapsed) → total_elapsed\n- SUM(manual_costs - automated_costs) → savings\n- time-series via generate_series()"]
    Serialize["Serialize to JSON\n(drf-spectacular schema)"]
    Response["200 OK {totals, chart_data, top_users, top_projects}"]

    Request --> Auth
    Auth --> Filters
    Filters --> Aggregate
    Aggregate --> Serialize
    Serialize --> Response
```

The details endpoint uses `django-generate-series` to produce **gap-free time-series buckets** from PostgreSQL's `generate_series()`. This ensures chart data always has a point for every time bucket in the selected range, even when no jobs ran.

---

## Database Schema (Key Tables)

```mermaid
erDiagram
    Cluster {
        int id PK
        string name
        string address
        int port
        string protocol
        bytes access_token_encrypted
        bytes refresh_token_encrypted
        string aap_version
    }

    Organization {
        int id PK
        int cluster_id FK
        string name
    }

    JobTemplate {
        int id PK
        int cluster_id FK
        int organization_id FK
        string name
        decimal time_taken_manually_execute_minutes
        decimal labor_cost_per_hour
        bool is_active
    }

    Job {
        int id PK
        int cluster_id FK
        int organization_id FK
        int job_template_id FK
        int project_id FK
        int inventory_id FK
        string status
        float elapsed
        int host_count
        datetime started
        datetime finished
    }

    JobHostSummary {
        int id PK
        int job_id FK
        int host_id FK
        bool failed
        int changed
    }

    JobLabel {
        int id PK
        int job_id FK
        int label_id FK
    }

    SubscriptionCost {
        int id PK
        decimal monthly_subscription_cost
        decimal engineer_hourly_rate
    }

    SyncSchedule {
        int id PK
        int cluster_id FK
        string rrule
        datetime last_run
    }

    SyncJob {
        int id PK
        int cluster_id FK
        string job_type
        string status
        datetime created_at
        datetime completed_at
    }

    ClusterSyncData {
        int id PK
        int cluster_id FK
        json raw_data
        datetime created_at
    }

    JwtUserToken {
        int id PK
        int user_id FK
        string access_token
        string refresh_token
        datetime expires_at
    }

    FilterSet {
        int id PK
        int user_id FK
        string name
        json filter_state
    }

    Cluster ||--o{ Organization : "has"
    Cluster ||--o{ JobTemplate : "has"
    Cluster ||--o{ Job : "has"
    Cluster ||--o{ SyncSchedule : "has"
    Cluster ||--o{ SyncJob : "has"
    Cluster ||--o{ ClusterSyncData : "has"
    Organization ||--o{ Job : "has"
    JobTemplate ||--o{ Job : "has"
    Job ||--o{ JobHostSummary : "has"
    Job ||--o{ JobLabel : "has"
```

---

## Scheduler Architecture

```mermaid
flowchart LR
    subgraph "Every 20s (periodic_scheduler)"
        CheckDue["Query SyncSchedule\nwhere next_run <= now()"]
        AdvisoryLock["Acquire pg advisory lock\n(lock_id = cluster.id)"]
        Fire["pg_notify sync channel\nfor each due schedule"]
        UpdateLastRun["Update SyncSchedule.last_run"]
    end

    subgraph "Every 5s (parse_scheduler)"
        CheckPending["Query SyncJob\nwhere status=PENDING\nand job_type=PARSE_JOB_DATA"]
        ParseLock["Acquire pg advisory lock\n(lock_id = syncjob.id)"]
        NotifyParse["pg_notify parse channel"]
    end

    subgraph "Every 20s (sync_task_manager)"
        SyncMgr["SyncTaskManager.schedule()\nreconciles stuck/failed jobs"]
    end

    CheckDue --> AdvisoryLock
    AdvisoryLock --> Fire
    Fire --> UpdateLastRun
    CheckPending --> ParseLock
    ParseLock --> NotifyParse
```

RRULE parsing is handled by `python-dateutil`. Each `SyncSchedule` stores a raw RFC 5545 RRULE string and a `last_run` timestamp; the scheduler computes the next occurrence and fires when it is due.

---

## Analytics and Metrics

```mermaid
graph LR
    subgraph "Prometheus Metrics (analytics/)"
        collectors["collectors.py\n(data collection)"]
        metrics_py["metrics.py\n(metric definitions:\nCounters, Gauges, Histograms)"]
        subsystem["subsystem_metrics.py\n(DispatcherMetrics)"]
        analytics_tasks["analytics_tasks.py\nsend_subsystem_metrics()\nevery 20s via dispatcherd"]
    end

    analytics_tasks -->|"pushes to"| PushGateway["Prometheus Pushgateway\n(or /api/v1/metrics/ pull)"]
    metrics_py -->|"exposed at"| MetricsEndpoint["GET /api/v1/metrics/"]
```

`DispatcherMetrics` tracks task queue depths, execution times, and sync success/failure rates. Metrics are exported both via the pull endpoint (`/api/v1/metrics/`) and pushed to a Pushgateway.

---

## Settings Layering

```mermaid
flowchart TD
    Base["settings.py\n(base: DB, JWT, CORS, dispatcherd channels, installed apps)"]
    Local["local_settings.py\n(gitignored: AAP_AUTH_PROVIDER OAuth2 creds)"]
    Prod["/etc/dashboard/conf.d/*.py\n(production overrides, loaded via split-settings)"]
    Test["tests/settings_for_test.py\n(--nomigrations, in-memory SQLite or test DB)"]

    Base --> Local
    Base --> Prod
    Base --> Test
```

`split-settings` loads all `*.py` files from `DASHBOARD_SETTINGS_DIR` at startup in production, allowing operators to drop override files without modifying the base image.

---

## Container Runtime

```mermaid
graph LR
    subgraph "Dockerfile.backend (3 stages)"
        Stage1["web-builder\nubi9/nodejs-22\nnpm run build → dist/"]
        Stage2["python-builder\nubi9/ubi-minimal\nbuild Python wheels (C/Rust)"]
        Stage3["final runtime\nubi9/ubi-minimal\n/venv (wheels)\ndist/ (SPA)\nnginx + uwsgi + supervisord"]
    end

    Stage1 -->|"copy dist/"| Stage3
    Stage2 -->|"copy wheels"| Stage3
    Stage3 -->|"dumb-init entrypoint"| Supervisord["supervisord\n├─ nginx (port 8053)\n└─ uwsgi (backend)"]
```

- Port 8053 is exposed — nginx answers HTTP on that port
- `dumb-init` is used as PID 1 to handle signal propagation correctly in containers
- `uwsgi` serves the Django app; nginx reverse-proxies `/api/` to it and serves the SPA for all other paths

---

## Key Source File Reference

| Area | File | Role |
|------|------|------|
| Settings | `src/backend/django_config/settings.py` | Base config |
| Root URLs | `src/backend/django_config/urls.py` | Route registration |
| Core models | `src/backend/apps/clusters/models.py` | All domain models |
| AAP connector | `src/backend/apps/clusters/connector.py` | HTTP calls to AAP |
| Data parser | `src/backend/apps/clusters/parser.py` | Raw JSON → Django models |
| Encryption | `src/backend/apps/clusters/encryption.py` | AES-256 cluster creds |
| OAuth2 client | `src/backend/apps/aap_auth/aap_auth.py` | Code exchange with AAP |
| JWT lifecycle | `src/backend/apps/aap_auth/jwt_token.py` | Token encode/decode/rotate |
| DRF auth class | `src/backend/apps/aap_auth/authentication.py` | Per-request auth |
| Scheduler models | `src/backend/apps/scheduler/models.py` | SyncSchedule, SyncJob |
| Dispatcher | `src/backend/apps/dispatch/dispatcherd.py` | DashboardTaskWorker |
| Sync task | `src/backend/apps/tasks/jobs.py` | AAPSyncTask, AAPParseDataTask |
| Periodic tasks | `src/backend/apps/tasks/system.py` | Scheduler heartbeat tasks |
| Report view | `src/backend/api/v1/report/views.py` | Main aggregation endpoint |
| API URLs | `src/backend/api/v1/urls.py` | Full API route map |
| Prometheus | `src/backend/analytics/metrics.py` | Metric definitions |
