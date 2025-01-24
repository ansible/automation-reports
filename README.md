# Automation reports

Hello! And welcome to the Automation reports monorepo.

### Running locally

## Backend
    python3.12 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip wheel
    pip install -r requirements.txt

#### Migrations and superuser
    python manage.py migrate
    python manage.py createsuperuser

#### Set up instances
    python manage.py setinstances <path to yaml file>

### Run
    python manage.py runserver

## Frontend
    yarn install
    yarn run start:dev
