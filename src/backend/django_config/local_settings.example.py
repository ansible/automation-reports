import os
DB_NAME = os.environ.get("DB_NAME", "aapdashboard")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("", "5432"))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    }
}

SECRET_KEY = 'django-insecure-cu=@gv*8$8+rr2-^-8^g00!ib_9-utgu!26#q#@)!y%3#wt^1#'
DATABASE_KEY = 'insecure-database-encryption-key-cu=@gv*8$8+rr2-^-8^g00!ib_9-utgu!26#q#@)!y%3#wt^1#'

AAP_AUTH_PROVIDER = {
    "name": "Ansible Automation Platform",
    "protocol": "https",
    #
    # For AAP v2.4
    "url": "aap24.example.com:8443/api",
    "user_data_endpoint": "/v2/me/",
    # For AAP v2.5, v2.6
    # "url": "aap25.example.com",
    # "user_data_endpoint": "/api/gateway/v1/me/",
    #
    "check_ssl": False,
    "client_id": "TODO",
    "client_secret": "TODO",
}

# Hide TLS warnings
# SHOW_URLLIB3_INSECURE_REQUEST_WARNING = False

# Enable Django debug
# Note - DEBUG=True also enables runserver to serve static files (usefull for admin site).
DEBUG = True
