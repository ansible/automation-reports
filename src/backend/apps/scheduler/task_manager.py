import logging
import signal
import time
import uuid

import redis
from ansible_base.lib.utils.db import advisory_lock
from django.conf import settings
from django.db import transaction

from backend.analytics.subsystem_metrics import DispatcherMetrics
from backend.apps.scheduler.models import SyncJob, JobTypeChoices, JobStatusChoices
from backend.apps.tasks.jobs import AAPSyncTask, AAPParseDataTask
from backend.common_utils import ScheduleSyncTaskManager, is_testing

logger = logging.getLogger('automation_dashboard.scheduler')


def timeit(func):
    def inner(*args, **kwargs):
        t_now = time.perf_counter()
        result = func(*args, **kwargs)
        dur = time.perf_counter() - t_now
        args[0].subsystem_metrics.inc(f"{args[0].prefix}_{func.__name__}_seconds", dur)
        return result

    return inner


class TaskBase:

    def __init__(self, prefix=""):
        self.all_tasks = None
        self.prefix = prefix
        self.start_task_limit = settings.START_TASK_LIMIT
        self.start_time = time.time()
        self.task_manager_timeout = settings.TASK_MANAGER_TIMEOUT
        self.subsystem_metrics = DispatcherMetrics(auto_pipe_execute=False)

        for m in self.subsystem_metrics.METRICS:
            if m.startswith(self.prefix):
                self.subsystem_metrics.set(m, 0)

    def timed_out(self):
        """Return True/False if we have met or exceeded the timeout for the task manager."""
        elapsed = time.time() - self.start_time
        if elapsed >= self.task_manager_timeout:
            logger.warning(
                f"{self.prefix} manager has run for {elapsed} which is greater than TASK_MANAGER_TIMEOUT of {settings.TASK_MANAGER_TIMEOUT}.")
            return True
        return False

    @timeit
    def get_tasks(self, filter_args):
        qs = SyncJob.objects.filter(**filter_args).order_by('internal_created').order_by('id')
        self.all_tasks = [t for t in qs]

    def get_local_metrics(self):
        data = {}
        for k, metric in self.subsystem_metrics.METRICS.items():
            if k.startswith(self.prefix) and metric.metric_has_changed:
                data[k[len(self.prefix) + 1:]] = metric.current_value
        return data

    def record_aggregate_metrics(self, *args):
        if is_testing():
            return
        try:
            DispatcherMetrics(auto_pipe_execute=True).inc(f"{self.prefix}__schedule_calls", 1)
            # Only record metrics if the last time recording was more
            # than SUBSYSTEM_METRICS_TASK_MANAGER_RECORD_INTERVAL ago.
            # Prevents a short-duration task manager that runs directly after a
            # long task manager to override useful metrics.
            current_time = time.time()
            time_last_recorded = current_time - self.subsystem_metrics.decode(f"{self.prefix}_recorded_timestamp")
            if time_last_recorded > settings.SUBSYSTEM_METRICS_TASK_MANAGER_RECORD_INTERVAL:
                logger.debug(f"recording {self.prefix} metrics, last recorded {time_last_recorded} seconds ago")
                self.subsystem_metrics.set(f"{self.prefix}_recorded_timestamp", current_time)
                self.subsystem_metrics.pipe_execute()
            else:
                logger.debug(
                    f"skipping recording {self.prefix} metrics, last recorded {time_last_recorded} seconds ago")
        except redis.exceptions.ConnectionError as exc:
            logger.warning(f"Redis connection error saving metrics for {self.prefix}, error: {exc}")
        except Exception:
            logger.exception(f"Error saving metrics for {self.prefix}")

    def schedule(self):
        # Always be able to restore the original signal handler if we finish
        original_sigusr1 = signal.getsignal(signal.SIGUSR1)
        lock_session_timeout_milliseconds = settings.TASK_MANAGER_LOCK_TIMEOUT * 1000  # convert to milliseconds
        with advisory_lock(f"{self.prefix}_lock", lock_session_timeout_milliseconds=lock_session_timeout_milliseconds,
                           wait=False) as acquired:
            with transaction.atomic():
                if acquired is False:
                    logger.debug(f"Not running {self.prefix} scheduler, another task holds lock")
                    return
                logger.debug(f"Starting {self.prefix} Scheduler")
                try:
                    self._schedule()
                finally:
                    signal.signal(signal.SIGUSR1, original_sigusr1)

                commit_start = time.time()
                logger.debug(f"Commiting {self.prefix} Scheduler changes")
                if self.prefix == "automation_dashboard_task_manager":
                    self.subsystem_metrics.set(f"{self.prefix}_commit_seconds", time.time() - commit_start)
                local_metrics = self.get_local_metrics()
                self.record_aggregate_metrics()

                logger.debug(f"Finished {self.prefix} Scheduler, timing data:\n{local_metrics}")


class SyncTaskManager(TaskBase):

    def __init__(self):
        super(SyncTaskManager, self).__init__(prefix="automation_dashboard_task_manager")

    @timeit
    def start_task(self, task):
        self.subsystem_metrics.inc(f"{self.prefix}_tasks_started", 1)
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

    @timeit
    def process_pending_tasks(self, pending_tasks):
        for task in pending_tasks:
            if self.start_task_limit <= 0:
                break
            if self.timed_out():
                logger.warning("Task manager has reached time out while processing pending jobs, exiting loop early")
                break
            self.start_task(task)

    def process_tasks(self):
        running_tasks = [t for t in self.all_tasks if t.status in [JobStatusChoices.WAITING, JobStatusChoices.RUNNING]]
        self.subsystem_metrics.inc(f"{self.prefix}_running_processed", len(running_tasks))
        pending_tasks = [t for t in self.all_tasks if t.status == JobStatusChoices.PENDING]
        self.subsystem_metrics.inc(f"{self.prefix}_pending_processed", len(pending_tasks))
        self.process_pending_tasks(pending_tasks)

    def _schedule(self):
        self.get_tasks(
            dict(
                status__in=[JobStatusChoices.PENDING, JobStatusChoices.WAITING, JobStatusChoices.RUNNING],
                type__in=[JobTypeChoices.SYNC_JOBS, JobTypeChoices.PARSE_JOB_DATA])
        )
        if len(self.all_tasks) > 0:
            self.process_tasks()
