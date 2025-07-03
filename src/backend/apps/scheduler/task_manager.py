import logging
import signal
import time
import uuid

from ansible_base.lib.utils.db import advisory_lock
from django.conf import settings
from django.db import transaction

from backend.apps.scheduler.models import SyncJob, JobTypeChoices, JobStatusChoices
from backend.apps.tasks.jobs import AAPSyncTask, AAPParseDataTask
from backend.common_utils import ScheduleSyncTaskManager

logger = logging.getLogger('automation_dashboard.scheduler')


class TaskBase:

    def __init__(self, prefix=""):
        self.all_tasks = None
        self.prefix = prefix
        self.start_task_limit = settings.START_TASK_LIMIT
        self.start_time = time.time()
        self.task_manager_timeout = settings.TASK_MANAGER_TIMEOUT

    def timed_out(self):
        """Return True/False if we have met or exceeded the timeout for the task manager."""
        elapsed = time.time() - self.start_time
        if elapsed >= self.task_manager_timeout:
            logger.warning(f"{self.prefix} manager has run for {elapsed} which is greater than TASK_MANAGER_TIMEOUT of {settings.TASK_MANAGER_TIMEOUT}.")
            return True
        return False

    def get_tasks(self, filter_args):
        qs = SyncJob.objects.filter(**filter_args).order_by('internal_created').order_by('id')
        self.all_tasks = [t for t in qs]

    def schedule(self):
        # Always be able to restore the original signal handler if we finish
        original_sigusr1 = signal.getsignal(signal.SIGUSR1)

        lock_session_timeout_milliseconds = settings.TASK_MANAGER_LOCK_TIMEOUT * 1000  # convert to milliseconds
        with advisory_lock(f"{self.prefix}_lock", lock_session_timeout_milliseconds=lock_session_timeout_milliseconds, wait=False) as acquired:
            with transaction.atomic():
                if acquired is False:
                    logger.debug(f"Not running {self.prefix} scheduler, another task holds lock")
                    return
                logger.debug(f"Starting {self.prefix} Scheduler")
                try:
                    self._schedule()
                finally:
                    signal.signal(signal.SIGUSR1, original_sigusr1)


class SyncTaskManager(TaskBase):

    def __init__(self):
        super(SyncTaskManager, self).__init__(prefix="sync_task_manager")

    def start_task(self, task):
        self.start_task_limit -= 1

        if self.start_task_limit == 0:
            # schedule another run immediately after this task manager
            ScheduleSyncTaskManager().schedule()

        task.status = JobStatusChoices.WAITING
        task.celery_task_id = str(uuid.uuid4())
        task.save()
        if task.type == JobTypeChoices.SYNC_JOBS:
            task_cls = AAPSyncTask
            task_cls.apply_async(
                [task.pk],
                {},
                queue=settings.DISPATCHER_SYNC_CHANNEL,
                uuid=task.celery_task_id,
            )
        elif task.type == JobTypeChoices.PARSE_JOB_DATA:
            task_cls = AAPParseDataTask
            task_cls.apply_async(
                [task.pk],
                {},
                queue=settings.DISPATCHER_PARSE_CHANNEL,
                uuid=task.celery_task_id,
            )
        else:
            msg = f"Unknown task type: {task.type}"
            logger.error(f"Unknown task type: {task.type}")
            task.status = JobStatusChoices.FAILED
            task.explanation = msg
            return

    def process_pending_tasks(self, pending_tasks):
        for task in pending_tasks:
            if self.start_task_limit <= 0:
                break
            if self.timed_out():
                logger.warning("Task manager has reached time out while processing pending jobs, exiting loop early")
                break
            self.start_task(task)

    def process_tasks(self):
        pending_tasks = [t for t in self.all_tasks if t.status == JobStatusChoices.PENDING]
        self.process_pending_tasks(pending_tasks)

    def _schedule(self):
        self.get_tasks(
            dict(
                status__in=[JobStatusChoices.PENDING, JobStatusChoices.WAITING, JobStatusChoices.RUNNING],
                type__in=[JobTypeChoices.SYNC_JOBS, JobTypeChoices.PARSE_JOB_DATA])
        )
        if len(self.all_tasks) > 0:
            self.process_tasks()
