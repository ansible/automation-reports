# Automation Dashboard

Hello! And welcome to the Automation Dashboard monorepo.

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

```bash
python manage.py syncdata --since=2025-02-12 --until=2025-02-12
```

### Run dramatiq

```bash
cd src/backend_workers
./periodic.py
```

### Tests

```bash
# set -o allexport; source .env; set +o allexport;

cd src/backend
cat <<EOF >django_config/local_settings.py
DB_NAME = "aapreports"
DB_USER = "root"
DB_PASSWORD = "TODO"
DB_HOST = "localhost"
DB_PORT = 5432
EOF
docker exec -it aapreport-db-1 psql -c 'ALTER USER root CREATEDB;'

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
```
