#!/usr/bin/env python3

import logging
import os
import sys
import urllib3
from datetime import datetime, timezone
from pathlib import Path
from time import sleep

import django
from crontab import CronTab

project_root = Path(os.path.realpath(__file__)).parent.parent
sys.path.insert(0, str(project_root))

os.environ.update(DJANGO_SETTINGS_MODULE="backend.django_config.settings")
os.environ.update(LOG_LEVEL="INFO")

cron_entry = os.environ.get("CRON_SYNC", "0 */4 * * *")

django.setup()
from django.conf import settings

logger = logging.getLogger("automation-reports")

entry = CronTab(cron_entry)

from backend.apps.clusters.models import Cluster, ClusterSyncData
from backend.apps.clusters.connector import ApiConnector
from backend.apps.clusters.parser import DataParser

if not settings.SHOW_URLLIB3_INSECURE_REQUEST_WARNING:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def run_task():
    job_start = datetime.now()
    logger.info("Starting sync task.")
    try:
        logger.info("Retrieving clusters information")
        clusters = Cluster.objects.all()
    except Exception as exc:
        logger.error(f"Failed to retrieve clusters information.", exc_info=exc)
        return

    for cluster in clusters:
        start = datetime.now()
        api = ApiConnector(cluster)
        try:
            logger.info(f"Retrieving data from cluster {cluster}")
            api.sync()
            end_sync = datetime.now()
            s = (end_sync - start).total_seconds()
            logger.info(f"Synced data from cluster {cluster} successfully in {s} seconds.")
        except Exception as exc:
            logger.error(f"Failed to sync cluster {cluster}", exc_info=exc)
            return

        sync_data = ClusterSyncData.objects.filter(cluster=cluster)
        count = sync_data.count()
        if count > 0:
            logger.info(f"Synced data parsing {sync_data.count()} job(s).")
            parser_start = datetime.now()
            for data in sync_data:
                try:
                    logger.info(f"Parsing data with id {data.id}.")
                    data_parser = DataParser(data.id)
                    data_parser.parse()
                    logger.info(f"Parsed data with id {data.id} successfully.")
                except Exception as exc:
                    logger.error(f"Failed to parse data {data.id}", exc_info=exc)
            parser_end = datetime.now()
            logger.info(f"Synced data parsing successfully in {(parser_end - parser_start).total_seconds()} seconds.")
        else:
            logger.info(f"No data for parse found.")
    job_end = datetime.now()
    logger.info(f"Finished sync task in {(job_end - job_start).total_seconds()} seconds.")


def get_next_run():
    current = datetime.now(timezone.utc)
    return entry.next(now=current, default_utc=True)


if __name__ == '__main__':
    run_task()
    while True:
        now = datetime.now(timezone.utc)
        next_run = get_next_run()
        if next_run < 1:
            run_task()
        sleep(1)
