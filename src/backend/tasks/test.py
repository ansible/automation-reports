import os
import sys
from datetime import datetime
from pathlib import Path
from time import sleep

import dramatiq
import django
from dramatiq.brokers.redis import RedisBroker

# from backend.apps.clusters.connector import ApiConnector
# from backend.apps.clusters.models import Cluster

# from backend.apps.clusters.connector import ApiConnector
# from backend.apps.clusters.models import Cluster

broker = RedisBroker(
    url="redis://localhost:6379/0",
)

project_root = Path(os.path.realpath(__file__)).parent.parent.parent
print(project_root)
sys.path.insert(0, str(project_root))
print(sys.path)
os.environ.update(DJANGO_SETTINGS_MODULE="backend.django_config.settings")

django.setup()
print(project_root)
from backend.apps.clusters.connector import ApiConnector
from backend.apps.clusters.models import Cluster


@dramatiq.actor
def test(message):
    print(f"Received message: {message}")
    # #sleep(10)  # Simulate work
    clusters = Cluster.objects.all()
    since  = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0, day=1, month=1)
    for cluster in clusters:
        print("Testing cluster", str(cluster))
        connector = ApiConnector(cluster, since=since)
        connector.sync()
    print("Task completed.")


if __name__ == "__main__":
    print("Starting test...")
    pass
