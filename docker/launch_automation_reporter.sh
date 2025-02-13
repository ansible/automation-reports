#!/bin/bash
# Script is started via dumb-init

nginx -g 'daemon off;' &
exec /venv/bin/python manage.py runserver 0.0.0.0:8000
