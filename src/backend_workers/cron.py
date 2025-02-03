#!/usr/bin/env python3


import os
import sys
import django
from time import sleep
from crontab import CronTab
from datetime import datetime, timezone
from pathlib import Path

#from backend_workers.workers import sync_clusters

cron_entry = os.environ.get("CRON_SYNC", "0 */4 * * *")

entry = CronTab(cron_entry)


project_root = Path(os.path.realpath(__file__)).parent.parent
sys.path.insert(0, str(project_root))
os.environ.update(DJANGO_SETTINGS_MODULE="backend.django_config.settings")

django.setup()

import logging

logger = logging.getLogger("automation-reports")

def do_work():
    print("Starting cron")
    #sync_clusters.send()

if __name__ == '__main__':
    now = datetime.now(timezone.utc)
    value = entry.next(now=now, default_utc=True)

    if value > 60:
        logger.info(f"Start sync server running at {now.isoformat()}")
        do_work()
    while True:
        now = datetime.now(timezone.utc)
        value = entry.next(now=now, default_utc=True)
        #sleep(value)
        if value < 1:
            logger.info(f"Start sync server running at {now}")
            do_work()
        sleep(1)
