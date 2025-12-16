import logging
from django.conf import settings
from django_guid.log_filters import CorrelationId
from django_guid import get_guid

from backend.common_utils import is_testing
from backend.constants import LOGGER_BLOCKLIST


def record_is_blocked(record):
    """Given a log record, return True if it is considered to be
    blocked, return False if not
    """
    for logger_name in LOGGER_BLOCKLIST:
        if record.name.startswith(logger_name):
            return True
    return False


class DynamicLevelFilter(logging.Filter):
    def filter(self, record):
        """Filters out logs that have a level below the threshold defined
        by the database setting LOG_AGGREGATOR_LEVEL
        """
        if record_is_blocked(record):
            # Fine to write denied loggers to file, apply default filtering level
            cutoff_level = logging.WARNING
        else:
            try:
                cutoff_level = logging._nameToLevel[settings.LOG_AGGREGATOR_LEVEL]
            except Exception:
                cutoff_level = logging.WARNING

        return bool(record.levelno >= cutoff_level)


class RequireDebugTrueOrTest(logging.Filter):
    """
    Logging filter to output when in DEBUG mode or running tests.
    """

    def filter(self, record):
        return settings.DEBUG or is_testing()


class DefaultCorrelationId(CorrelationId):
    def filter(self, record):
        guid = get_guid() or '-'
        record.guid = guid
        return True
