import logging

from backend.apps.clusters.models import JobStatusChoices
from backend.apps.scheduler.models import SyncSchedule, SyncJob


def _run_dispatch_startup_common():
    """
    Execute the common startup initialization steps.
    This includes updating schedules.
    """
    startup_logger = logging.getLogger('automation_dashboard.tasks')

    for sch in SyncSchedule.objects.all():
        try:
            sch.update_computed_fields()
        except Exception:
            startup_logger.exception("Failed to rebuild schedule %s.", sch)


def redo_unfinished_tasks():
    """
    Reset jobs (waiting, running) in case the server was shut down so they can be restarted.
    """
    tasks = SyncJob.objects.filter(status__in=[JobStatusChoices.WAITING, JobStatusChoices.RUNNING])
    for task in tasks:
        task.status = JobStatusChoices.PENDING
        task.started = None
        task.finished = None
        task.elapsed = 0
        task.save()


def dispatch_startup():
    _run_dispatch_startup_common()
    redo_unfinished_tasks()
