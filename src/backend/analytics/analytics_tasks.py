from dispatcherd.publish import task
from django.conf import settings

from backend.analytics.subsystem_metrics import DispatcherMetrics


@task(queue=settings.DISPATCHER_METRICS_CHANNEL, timeout=300, on_duplicate='discard')
def send_subsystem_metrics():
    DispatcherMetrics().send_metrics()
