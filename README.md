# Automation reports

Hello! And welcome to the Automation reports monorepo.

### Running locally

## Backend

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt
```

#### Migrations and superuser

```bash
python manage.py migrate
python manage.py createsuperuser
```

#### Set up instances

```bash
python manage.py setinstances <path to yaml file>
```

### Run

```bash
python manage.py runserver
```

## Frontend

```bash
yarn install
yarn run start:dev
```
