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
