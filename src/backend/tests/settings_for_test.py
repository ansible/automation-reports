# Python
import uuid
from backend.django_config.settings import *

# Turn off task submission, because sqlite3 does not have pg_notify
DISPATCHER_MOCK_PUBLISH = True


CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'unique-{}'.format(str(uuid.uuid4()))}}
TEST_DATABASE_PREFIX = 'test'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    },
    'TEST': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': f'{TEST_DATABASE_PREFIX}_{DB_NAME}',
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    }
}


LOG_LEVEL = 'ERROR'
# Default Time taken to manually execute automation (min)
DEFAULT_TIME_TAKEN_TO_MANUALLY_EXECUTE_MINUTES = 60

# Default Time taken to manually create automation (min)
DEFAULT_TIME_TAKEN_TO_CREATE_AUTOMATION_MINUTES = 60

#Default average cost of an employee per minute
DEFAULT_MANUAL_COST_AUTOMATION = 50

#Deafult cost per minute of AAP
DEFAULT_AUTOMATED_PROCESS_COST = 20

START_TASK_LIMIT = 5
TASK_MANAGER_TIMEOUT = 3
TASK_MANAGER_TIMEOUT_GRACE_PERIOD = 6
TASK_MANAGER_LOCK_TIMEOUT = TASK_MANAGER_TIMEOUT + TASK_MANAGER_TIMEOUT_GRACE_PERIOD

JWT_ACCESS_TOKEN_LIFETIME_SECONDS = 60
JWT_REFRESH_TOKEN_LIFETIME_SECONDS = 7200

AAP_AUTH_PROVIDER = {
    'name': 'test_name',
    'protocol': 'https',
    'url': 'localhost',
    'user_data_endpoint': '/api/v1/me/',
    'check_ssl': False,
    'client_id': 'test_client_id',
    'client_secret': 'test_client_secret',
}
