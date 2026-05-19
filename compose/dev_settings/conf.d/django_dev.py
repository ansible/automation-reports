import os

with open('/etc/dashboard/SECRET_KEY') as f:
    SECRET_KEY = f.read().strip()

with open('/etc/dashboard/DATABASE_KEY') as f:
    DATABASE_KEY = f.read().strip()

# AAP auth not configured yet — setup wizard handles this
AAP_AUTH_PROVIDER_CLIENT_SECRET = ''
AAP_AUTH_PROVIDER = {
    'name': 'Ansible Automation Platform',
    'protocol': 'https',
    'url': 'http://localhost',
    'user_data_endpoint': 'http://localhost',
    'check_ssl': False,
    'client_id': '',
    'client_secret': '',
}

ALLOWED_HOSTS = ['*']
DEBUG = True

# Enable local-account login for the compose dev environment.
# Never set this in production.
ALLOW_DEV_LOGIN = True

# Redis via TCP (not unix socket as in the Ansible installer)
BROKER_URL = 'redis://redis:6379/0'

SHOW_URLLIB3_INSECURE_REQUEST_WARNING = False
INITIAL_SYNC_DAYS = 1
WEASYPRINT_BASEURL = '/code/src/backend/templates'
JWT_ACCESS_TOKEN_LIFETIME_SECONDS = 3600
JWT_REFRESH_TOKEN_LIFETIME_SECONDS = 86400

CORS_ALLOWED_ORIGINS = ['http://localhost:8083', 'http://localhost:9000']
