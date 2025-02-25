#!/bin/bash
# Script is started via dumb-init

nginx -g 'daemon off;' &
/venv/bin/python manage.py runserver 0.0.0.0:8000 &
exec sleep inf
