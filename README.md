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
The python backend will be accessible on http://localhost:8000.
The website frontend will be accessible on http://localhost:9000.

If python backend or website frontend runs on a different URL, instructions need to be adjusted.

#### Prerequisites - AAP OAuth2 application and token

We need to create OAuth2 application and access token for integration with AAP.
Follow [setup/README.md](setup/README.md#sso-authentication), section "SSO authentication".
The AAP OAuth2 application requires a redirect URL.

The redirect URL for the AAP OAuth2 application needs to point to URL where you Automation Dashboard frontend is accessible.
In this development setup we run frontend on localhost, on port 9000.
Thus the redirect URL is http://localhost:9000/auth-callback.

#### Backend

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

Create `local_settings.py` file.
Review file. The content needs to be adjusted.
In particular, the `AAP_AUTH_PROVIDER` variable needs to be populated.

```bash
cp -i src/backend/django_config/local_settings.example.py src/backend/django_config/local_settings.py
nano src/backend/django_config/local_settings.py
```

#### Migrations and superuser

```bash
cp -i .env.example .env
source .env
(cd compose; docker compose --project-directory .. -f compose.yml up --build db)

cd src/backend
export PYTHONPATH=$PWD/.. # pip install -e .

python manage.py migrate
python manage.py createsuperuser
```

#### Set up instances

File `clusters.yaml` needs to contain the AAP access token.

```bash
cp -i clusters.example.yaml clusters.yaml
nano clusters.yaml
python manage.py setclusters <path to yaml file>
```

### Run

```bash
python manage.py runserver
```

### Sync AAP data

The sync process now creates background tasks that are processed by the dispatcher:

```bash
# Create a sync task for a specific date range
python manage.py syncdata --since=2025-02-12 --until=2025-02-12

# Without date range, it will prompt for confirmation (syncs from last sync date)
python manage.py syncdata
```

### Run the Task Dispatcher

The dispatcher processes all background tasks including data syncs and parsing:

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

**Note**: The dispatcher must be running for sync tasks to be processed. In production, this should be run as a separate service.

### Tests

```bash
# source .env

cd src/backend
cat django_config/local_settings.py  # review content
docker exec -it aapdashboard-db-1 psql -c 'ALTER USER root CREATEDB;'

export PYTHONPATH=$PWD/.. # pip install -e .
pytest --cov=backend
```

## Frontend

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

If only blank page is visible at URL http://localhost:9000/, check browser console for errors.
Error `Error: Missing API url` means VITE_API_URL is not set.
Fix this by loading `.env` file content - `set -o allexport; source .env; set +o allexport`).

## Task ManagerPerformance Tuning

- `JOB_EVENT_WORKERS`: Number of processes for event processing (default: 4)
- `SCHEDULE_MAX_DATA_PARSE_JOBS`: Maximum concurrent parse jobs (default: 30)
- `DISPATCHER_DB_DOWNTIME_TOLERANCE`: Database reconnection timeout (default: 40 seconds)
