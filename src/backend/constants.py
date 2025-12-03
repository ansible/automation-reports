# loggers that may be called in process of emitting a log
LOGGER_BLOCKLIST = (
    'automation_dashboard.utils.filters',
    # dispatcherd should only use 1 database connection
    'dispatcherd',
)