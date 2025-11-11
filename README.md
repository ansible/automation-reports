# Automation Dashboard

Hello! And welcome to the Automation Dashboard monorepo.

## Architecture Overview

The Automation Dashboard uses a distributed task processing architecture:

- **Django Backend**: REST API and data models
- **Dispatcherd**: Task dispatcher for background job processing
- **PostgreSQL**: Database for storing job data and metrics
- **React Frontend**: Dashboard UI for visualizations

### Task Processing

The application uses `dispatcherd` (replacing the previous `dramatiq` implementation) to handle:

- Periodic synchronization of job data from AAP clusters
- Background parsing and processing of job metrics
- Scheduled task execution based on defined schedules

### Running locally

The instructions assume commands will be executed on developers laptop.
The python backend will be accessible on <http://localhost:8000>.
The website frontend will be accessible on <http://localhost:9000>.

If python backend or website frontend runs on a different URL, instructions need to be adjusted.

#### Prerequisites - AAP OAuth2 application and token

We need to create OAuth2 application and access token for integration with AAP.
Follow [setup/README.md](setup/README.md#sso-authentication), section "SSO authentication".
The AAP OAuth2 application requires a redirect URL.

The redirect URL for the AAP OAuth2 application needs to point to URL where you Automation Dashboard frontend is accessible.
In this development setup we run frontend on localhost, on port 9000.
Thus the redirect URL is <http://localhost:9000/auth-callback>.

## Service Dependencies Overview

The Automation Dashboard requires multiple services to run properly. Here's the recommended startup order:

1. **Database (Docker)** - Must be running first
2. **Django Backend** - Required for all API functionality and admin interface
3. **Task Dispatcher** - Required for background sync tasks to be processed
4. **Frontend** - Requires Django backend to be running

**Important Notes:**

- The **dispatcher must be running** for sync tasks to actually complete
- The **Django backend must be running** for the frontend to work properly
- Sync tasks created by `syncdata` commands will queue but won't process until the dispatcher is running

## Backend

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt
```

You might need to install required development libraries

```bash
# Fedora
sudo dnf install python3.12-devel libpq-devel
```

### Common Terminal Setup

Throughout this guide, you'll need to prepare your terminal environment. Here's the standard pattern:

```bash
# Navigate to project directory
cd /path/to/automation-reports

# Activate virtual environment
source .venv/bin/activate

# Load environment variables
source .env

# Navigate to backend and set Python path
cd src/backend
export PYTHONPATH=$PWD/..
```

**Note:** The sections below will reference "prepare your terminal" to mean running these commands.

### Start Docker Database

First, start the PostgreSQL database in Docker:

```bash
cp -i .env.example .env
source .env
(cd compose; docker compose --project-directory .. -f compose.yml up --build db)
```

### Migrations and superuser

Open a **new terminal**, prepare your terminal (see Common Terminal Setup above), and run:

```bash
python manage.py migrate
python manage.py createsuperuser
```

### Set up AAP Clusters Configuration

We need to create OAuth2 application and access token for integration with AAP.
Follow [setup/README.md](setup/README.md#sso-authentication), section "SSO authentication".

Create and configure the `clusters.yaml` file with your AAP cluster details:

```bash
cp -i clusters.example.yaml clusters.yaml
nano clusters.yaml
```

**Edit the following variables in `clusters.yaml`:**

- `address`: Change to your AAP VM IP address (e.g., `10.44.17.179`)
- `port`: Change value if your AAP API is accessible on a different TCP port.
- `client_id`: Replace `sampleClientId` with your actual AAP OAuth2 Application client ID
- `client_secret`: Replace `sampleClientSecret` with your actual AAP OAuth2 Application client secret
- `access_token`: Replace `sampleToken` with your actual AAP access token
- `refresh_token`: Replace `sampleRefreshToken` with your actual AAP refresh token
- Remove any unused cluster instances from the file

**About sync schedules:** The `sync_schedules` section in `clusters.yaml` automatically creates background sync tasks when loaded. Each schedule defines:

- `name`: A descriptive name for the sync task
- `rrule`: A recurrence rule (RFC 5545 format) that defines when syncing occurs
- `enabled`: Whether this sync schedule is active

Example configuration:

```yaml
---
clusters:
  - protocol: https
    address: 10.44.17.179  # Your AAP VM IP
    port: 8443             # change to 443
    client_id: sampleClientId # Actual client id
    client_secret: sampleClientSecret # Actual client secret
    access_token: sampleToken # Actual access token
    refresh_token: sampleRefreshToken # Actual refresh token
    verify_ssl: false
    sync_schedules:
      - name: Every 5 minutes sync
        rrule: DTSTART;TZID=Europe/Ljubljana:20250630T070000 FREQ=MINUTELY;INTERVAL=5
        enabled: true
      # You can add multiple sync schedules:
      # - name: Hourly sync
      #   rrule: DTSTART;TZID=Europe/Ljubljana:20250630T070000 FREQ=HOURLY;INTERVAL=1
      #   enabled: false
```

Then load the cluster configuration (prepare your terminal first):

```bash
python manage.py setclusters clusters.yaml
```

Note that when access token expires, the refresh token is used to obtain new access token.
At the same time the AAP returns also new refresh token.
The Automation Dashboard internally updates both values.
Implications:

- after token refresh happens, if you need to run `manage.py setclusters` again, you need to create a new token.
- The same access and refresh tokens can be used only by one Automation Dashboard installation

### Setup SSO login with AAP

Configure OAuth2 authentication by editing the `local_settings.py` file:

```bash
cd src/backend/django_config/
cp -i local_settings.example.py local_settings.py
nano local_settings.py
```

**Edit the following variables in `local_settings.py`:**

- `url`: Change from `aap.example.com` to your AAP VM IP
- `user_data_endpoint`: Change from `/api/v2/me/` to `/api/gateway/v1/me/` for AAP v2.5
- `client_id`: Replace `"TODO"` with your OAuth application client ID
- `client_secret`: Replace `"TODO"` with your OAuth application client secret

Example configuration:

```python
AAP_AUTH_PROVIDER = {
    "name": "AnsibleAutomationPlatform",
    "protocol": "https",
    "url": "aap.example.com",
    #
    # For AAP v2.4
    "user_data_endpoint": "/v2/me/",
    # For AAP v2.5, v2.6
    # "user_data_endpoint": "/api/gateway/v1/me/",
    #
    "check_ssl": False,
    "client_id": "TODO",  # Your OAuth client ID
    "client_secret": "TODO",  # Your OAuth client secret
}
```

### Run Development Server

Open a **new terminal**, prepare your terminal, and start the Django development server:

```bash
python manage.py runserver
```

### Sync AAP data

The sync process now creates background tasks that are processed by the dispatcher.

Open a **new terminal**, prepare your terminal, and run sync commands:

```bash
# Create a sync task for a specific date range
python manage.py syncdata --since=2025-02-12 --until=2025-02-12

# Without date range, it will prompt for confirmation (syncs from last sync date)
python manage.py syncdata
```

### Run the Task Dispatcher

The dispatcher processes all background tasks including data syncs and parsing.

Automation Dashboard administrator is required to setup a scheduled task.
Open <https://HOST:8447/admin/scheduler/syncschedule/> and click "Add sync schedule":

- name: `5 minutes`
- enabled: true
- rrule: `DTSTART;TZID=Europe/Ljubljana:20250630T070000 FREQ=MINUTELY;INTERVAL=5`
- cluster: select your cluster

Open a **new terminal**, prepare your terminal, and run the dispatcher:

```bash
# Start the dispatcher service
python manage.py run_dispatcher

# Check dispatcher status
python manage.py run_dispatcher --status

# View running tasks
python manage.py run_dispatcher --running

# Cancel a specific task
python manage.py run_dispatcher --cancel <task_uuid>
```

**Important**:

- The dispatcher must be running for sync tasks to be processed
- Any sync tasks created by `syncdata` commands will queue but won't execute until the dispatcher is running
- In production, this should be run as a separate service
- The Django backend should be running before starting the dispatcher

### Tests

Run backend tests in a **new terminal**. Prepare your terminal, then run:

```bash
# Review local settings content
cat django_config/local_settings.py

# Grant database creation permissions for tests
docker exec -it aapdashboard-db-1 psql -c 'ALTER USER root CREATEDB;'

# Run tests with coverage
pytest --cov=backend
```

### Requirements Management

This project uses automated requirements management. See [REQUIREMENTS.md](REQUIREMENTS.md) for detailed information.

**Quick commands:**
```bash
# Sync requirements files (creates venv if needed)
make sync-requirements

# Check if requirements are in sync
make requirements-check
```

### Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality and automatically sync requirements files:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks on all files
pre-commit run --all-files

# Run hooks manually
pre-commit run
```

The pre-commit configuration automatically:
- Syncs requirements files when `requirements-pinned.txt` changes
- Ensures requirements files are always up-to-date before commits

## Frontend

**Prerequisites**: Ensure the Django backend is running before starting the frontend (see backend setup above).

```bash
nvm use v22
npm --version
cd src/frontend
npm install
npm run start:dev

# run frontend tests
npx playwright install chromium
npx playwright test --headed
```

If only blank page is visible at URL <http://localhost:9000/>, check browser console for errors.
Error `Error: Missing API url` means VITE_API_URL is not set.
Fix this by loading `.env` file content - `set -o allexport; source .env; set +o allexport`.

## Performance Tuning

- `JOB_EVENT_WORKERS`: Number of processes for event processing (default: 4)
- `SCHEDULE_MAX_DATA_PARSE_JOBS`: Maximum concurrent parse jobs (default: 30)
- `DISPATCHER_DB_DOWNTIME_TOLERANCE`: Database reconnection timeout (default: 40 seconds)
