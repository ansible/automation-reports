import os
import sys
from datetime import datetime
from pathlib import Path

import dramatiq
import django
from dramatiq.brokers.redis import RedisBroker

redis_host = os.environ.get("SHARED_REDIS_HOST", "localhost")
redis_port = os.environ.get("SHARED_REDIS_PORT", "6379")

def get_broker():
    _broker = RedisBroker(
        host=redis_host,
        port=int(redis_port),
    )
    _broker.declare_queue("automation-reports-sync-data")
    _broker.declare_queue("automation-reports-parse-data")
    return _broker

broker = get_broker()

project_root = Path(os.path.realpath(__file__)).parent.parent
sys.path.insert(0, str(project_root))
os.environ.update(DJANGO_SETTINGS_MODULE="backend.django_config.settings")

django.setup()

import logging

logger = logging.getLogger("automation-reports")

@dramatiq.actor(queue_name="automation-reports-sync-data", max_retries=0, priority=30)
def sync_clusters():
    from backend.apps.clusters.connector import ApiConnector
    from backend.apps.clusters.models import Cluster

    clusters = Cluster.objects.all()
    since = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0, day=1, month=1)
    for cluster in clusters:
        logger.info(f"Starting sync cluster {cluster}")
        connector = ApiConnector(cluster, since=since)
        connector.sync()
        logger.info(f"Finished sync cluster {cluster}")
    logger.info("Sync clusters all done")


@dramatiq.actor(queue_name="automation-reports-parse-data", max_retries=0, priority=50)
def process_job_data(pk):
    from backend.apps.clusters.parser import DataParser
    logger.info(f"Processing pk {pk}")
    parser = DataParser(pk)
    parser.parse()
    logger.info(f"Finished processing pk {pk}")
