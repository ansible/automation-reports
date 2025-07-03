import django

# dispatcherd publisher logic is likely to be used, but needs manual preload
from dispatcherd.brokers import pg_notify  # noqa

# Cache may not be initialized until we are in the worker, so preload here
from channels_redis import core  # noqa
from dispatcherd.utils import resolve_callable

django.setup()

from django.conf import settings

# Preload all periodic tasks so their imports will be in shared memory
for name, options in settings.CELERYBEAT_SCHEDULE.items():
    resolve_callable(options['task'])

from django.core.cache import cache as django_cache
from django.db import connection

connection.close()
django_cache.close()
