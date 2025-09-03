#!/bin/bash
# Script is started via dumb-init

##!/usr/bin/env bash
#if [ `id -u` -ge 500 ]; then
#    echo "awx:x:`id -u`:`id -g`:,,,:/var/lib/awx:/bin/bash" >> /tmp/passwd
#    cat /tmp/passwd > /etc/passwd
#    rm /tmp/passwd
#fi

nginx -g 'daemon off;' &
/venv/bin/python manage.py runserver 0.0.0.0:8000 &
exec sleep inf
