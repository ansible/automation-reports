DB_NAME = "aapdashboard"
DB_USER = "root"
DB_PASSWORD = "TODO"
DB_HOST = "localhost"
DB_PORT = 5432

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

AAP_AUTH_PROVIDER = {
    "name": "AnsibleAutomationPlatform",
    "protocol": "https",
    #
    # For AAP v2.4
    "url": "aap24.example.com:8443/api",
    "user_data_endpoint": "/v2/me/",
    # For AAP v2.5
    # "url": "aap25.example.com",
    # "user_data_endpoint": "/api/v2/me/",
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
