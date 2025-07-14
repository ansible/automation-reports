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

#### Migrations and superuser

```bash
cp -i .env.example .env
set -o allexport; source .env; set +o allexport;
(cd compose; docker compose --project-directory .. -f compose.yml up --build db)

cd src/backend
export PYTHONPATH=$PWD/.. # pip install -e .

python manage.py migrate
python manage.py createsuperuser
```

#### Set up instances

```bash
cp -i clusters.example.yaml clusters.yaml
nano clusters.yaml
python manage.py setclusters <path to yaml file>
```

File `clusters.yaml` needs to contain an AAP OAuth2 application and token.
Create OAuth2 application at https://AAP_CONTROLLER_FQDN:8443/#/applications:

- Authorization grant type: Resource owner password-based
- Organization: Default
- Redirect URIs: empty
- Client type: Confidential

Create token at https://AAP_CONTROLLER_FQDN:8443/#/users/<id>/tokens:

- Scope: read

Store access token and refresh token value.
The access token is used in clusters.yaml.

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

## Frontend

```bash
yarn --version  # 3.8.6
cd src/frontend
yarn install
yarn run start:dev
```

## Task ManagerPerformance Tuning

- `JOB_EVENT_WORKERS`: Number of processes for event processing (default: 4)
- `SCHEDULE_MAX_DATA_PARSE_JOBS`: Maximum concurrent parse jobs (default: 30)
- `DISPATCHER_DB_DOWNTIME_TOLERANCE`: Database reconnection timeout (default: 40 seconds)
