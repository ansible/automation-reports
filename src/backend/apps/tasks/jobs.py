import logging
import time

from dispatcherd.publish import task
from dispatcherd.worker.exceptions import DispatcherCancel
from django.conf import settings
from django.db import transaction

from backend.analytics.subsystem_metrics import DispatcherMetrics
from backend.apps.clusters.connector import ApiConnector
from backend.apps.clusters.models import JobStatusChoices
from backend.apps.clusters.parser import DataParser
from backend.apps.scheduler.models import SyncJob
from backend.utils.update_models import update_model

logger = logging.getLogger('automation_dashboard.tasks.jobs')


class BaseTask(object):
    model = None
    abstract = True
    prefix = ""

    def __init__(self):
        # The .instance attribute will hold the SyncJob instance after run() is called.
        # The run() method requires the pk parameter to fetch the SyncJob from the database,
        # since self.instance is not set until after the job is loaded.
        self.instance = None
        self.cluster = None
        self.update_attempts = int(
            getattr(settings, 'DISPATCHER_DB_DOWNTOWN_TOLERANCE', settings.DISPATCHER_DB_DOWNTIME_TOLERANCE) / 5)
        self.subsystem_metrics = DispatcherMetrics(auto_pipe_execute=False)
        for m in self.subsystem_metrics.METRICS:
            if m.startswith(self.prefix):
                self.subsystem_metrics.set(m, 0)

    def update_model(self, pk, _attempt=0, **updates):
        status = updates.get('status', None)
        if status == JobStatusChoices.FAILED:
            self.subsystem_metrics.inc(f"{self.prefix}_tasks_failed", 1)
        elif status == JobStatusChoices.CANCELED:
            self.subsystem_metrics.inc(f"{self.prefix}_tasks_failed", 1)
        elif status == JobStatusChoices.SUCCESSFUL:
            self.subsystem_metrics.inc(f"{self.prefix}_tasks_succeeded", 1)
        return update_model(self.model, pk, _attempt=0, _max_attempts=self.update_attempts, **updates)

    def transition_status(self, pk: int) -> bool:
        """Atomically transition status to running, if False returned, another process got it"""
        with transaction.atomic():
            instance_data = SyncJob.objects.select_for_update(of=('self',)).get(pk=pk)
            if instance_data.status == JobStatusChoices.WAITING:
                instance_data.status = JobStatusChoices.RUNNING
                instance_data.save()
            elif instance_data.status == JobStatusChoices.RUNNING:
                logger.info(f'Job {pk} is being ran by another process, exiting')
                return False
        return True

    def run_task(self):
        pass

    def after_cancel_task(self):
        logger.info(f'Job {self.instance.pk} was canceled.')
        self.update_model(self.instance.pk, status=JobStatusChoices.CANCELED, explanation="Canceled")

    def run(self, pk, **kwargs):
        time_start = time.time()
        if self.instance is None:
            if not self.transition_status(pk):
                logger.info(f'Job {pk} is being ran by another process, exiting')
                return
        # Load the instance
        self.instance = self.update_model(pk)
        self.cluster = self.instance.cluster
        if self.instance.status != JobStatusChoices.RUNNING:
            logger.error(
                f'Not starting {self.instance.status} task pk={pk} because its status "{self.instance.status}" is not expected')
            return
        self.subsystem_metrics.inc(f"{self.prefix}_tasks_started", 1)
        self.run_task()
        elapsed = time.time() - time_start
        self.subsystem_metrics.inc(f"{self.prefix}_tasks_duration_seconds", elapsed)


@task(queue=settings.DISPATCHER_SYNC_CHANNEL)
class AAPSyncTask(BaseTask):
    model = SyncJob
    prefix = "automation_dashboard_sync_job"

    def run_task(self):
        job_args = self.instance.get_job_args

        if job_args is None:
            msg = f"No job args provided for task {self.instance.name}"
            logger.error(msg)
            self.update_model(self.instance.pk, status=JobStatusChoices.FAILED, explanation=msg)
            return

        connector = ApiConnector(self.cluster, **job_args)

        ### Check AAP version an if theserver is alive
        try:
            is_valid_aap_version = connector.check_aap_version()
        except DispatcherCancel:
            self.after_cancel_task()
            return
        except Exception:
            msg = f'Error connecting to AAP API: {self.cluster.base_url}'
            logger.exception("Failed to check AAP version")
            self.update_model(self.instance.pk, status=JobStatusChoices.FAILED, explanation=msg)
            return
        if not is_valid_aap_version:
            msg = f'Not valid version for cluster {self.cluster.base_url}.'
            logger.error(msg)
            self.update_model(self.instance.pk, status=JobStatusChoices.FAILED, explanation=msg)
            return

        ### Sync AAP organizations
        try:
            connector.sync_common('organization')
        except DispatcherCancel:
            self.after_cancel_task()
            return
        except Exception:
            msg = 'Failed to sync AAP Organizations.'
            logger.exception(msg)
            self.update_model(self.instance.pk, status=JobStatusChoices.FAILED, explanation=msg)
            return

        ### Sync AAP job templates
        try:
            connector.sync_common('job_template')
        except DispatcherCancel:
            self.after_cancel_task()
            return
        except Exception:
            msg = 'Failed to sync AAP Job templates.'
            logger.exception(msg)
            self.update_model(self.instance.pk, status=JobStatusChoices.FAILED, explanation=msg)
            return

        ## Sync AAP jobs
        try:
            connector.sync_jobs()
        except DispatcherCancel:
            self.after_cancel_task()
            return
        except Exception:
            msg = 'Failed to sync AAP Jobs.'
            logger.exception(msg)
            self.update_model(self.instance.pk, status=JobStatusChoices.FAILED, explanation=msg)
            return

        self.update_model(self.instance.pk, status=JobStatusChoices.SUCCESSFUL)


@task(queue=settings.DISPATCHER_PARSE_CHANNEL)
class AAPParseDataTask(BaseTask):
    model = SyncJob
    prefix = "automation_dashboard_parse_job"

    def run_task(self):
        sync_data = self.instance.cluster_sync_data
        if sync_data is None:
            msg = 'Synchronization data not available.'
            logger.exception(msg)
            self.update_model(self.instance.pk, status=JobStatusChoices.FAILED, explanation=msg)
            return

        data_parser = DataParser(sync_data.id)
        try:
            data_parser.parse()
        except DispatcherCancel:
            self.after_cancel_task()
            return
        except Exception:
            msg = f'Failed to parse AAP sync data: {sync_data.id}'
            logger.exception(msg)
            self.update_model(self.instance.pk, status=JobStatusChoices.FAILED, explanation=msg)
            return

        self.update_model(self.instance.pk, status=JobStatusChoices.SUCCESSFUL)
