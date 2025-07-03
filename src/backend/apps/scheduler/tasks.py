from dispatcherd.publish import task
from django.conf import settings

from backend.apps.scheduler.task_manager import SyncTaskManager


def run_manager(manager):
    manager().schedule()


@task(queue=settings.DISPATCHER_SYNC_CHANNEL)
def sync_task_manager():
    run_manager(SyncTaskManager)
