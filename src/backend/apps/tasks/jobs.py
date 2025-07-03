import logging

from dispatcherd.publish import task
from django.db import transaction

from backend.apps.clusters.connector import ApiConnector
from backend.apps.clusters.models import JobStatusChoices
from backend.apps.clusters.parser import DataParser
from backend.apps.scheduler.models import SyncJob
from backend.django_config import settings
from backend.utils.update_models import update_model

logger = logging.getLogger('automation_dashboard.tasks.jobs')


class BaseTask(object):
    model = None
    abstract = True

    def __init__(self):
        self.instance = None
        self.cluster = None
        self.update_attempts = int(getattr(settings, 'DISPATCHER_DB_DOWNTOWN_TOLERANCE', settings.DISPATCHER_DB_DOWNTIME_TOLERANCE) / 5)

    def update_model(self, pk, _attempt=0, **updates):
        return update_model(self.model, pk, _attempt=0, _max_attempts=self.update_attempts, **updates)

    def transition_status(self, pk: int) -> bool:
        """Atomically transition status to running, if False returned, another process got it"""
        with transaction.atomic():
            instance_data = SyncJob.objects.select_for_update(of=('self',)).get(pk=pk)
            if instance_data.status == JobStatusChoices.WAITING:
                instance_data.status = JobStatusChoices.RUNNING
                instance_data.save()
            elif instance_data['status'] == JobStatusChoices.RUNNING:
                logger.info(f'Job {pk} is being ran by another process, exiting')
                return False
        return True

    def run_task(self):
        pass

    def run(self, pk, **kwargs):
        if self.instance is None:
            if not self.transition_status(pk):
                logger.info(f'Job {pk} is being ran by another process, exiting')
                return
        # Load the instance
        self.instance = self.update_model(pk)
        self.cluster = self.instance.cluster
        if self.instance.status != JobStatusChoices.RUNNING:
            logger.error(f'Not starting {self.instance.status} task pk={pk} because its status "{self.instance.status}" is not expected')
            return
        self.run_task()


@task(queue=settings.DISPATCHER_SYNC_CHANNEL)
class AAPSyncTask(BaseTask):
    model = SyncJob

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
        except Exception:
            msg = 'Failed to sync AAP Organizations.'
            logger.exception(msg)
            self.update_model(self.instance.pk, status=JobStatusChoices.FAILED, explanation=msg)
            return

        ### Sync AAP job templates
        try:
            connector.sync_common('job_template')
        except Exception:
            msg = 'Failed to sync AAP Job templates.'
            logger.exception(msg)
            self.update_model(self.instance.pk, status=JobStatusChoices.FAILED, explanation=msg)
            return
        ## Sync AAP jobs

        try:
            connector.sync_jobs()
        except Exception:
            msg = 'Failed to sync AAP Jobs.'
            logger.exception(msg)
            self.update_model(self.instance.pk, status=JobStatusChoices.FAILED, explanation=msg)
            return

        self.update_model(self.instance.pk, status=JobStatusChoices.SUCCESSFUL)


@task(queue=settings.DISPATCHER_PARSE_CHANNEL)
class AAPParseDataTask(BaseTask):
    model = SyncJob

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
        except Exception:
            msg = f'Failed to parse AAP sync data: {sync_data.id}'
            logger.exception(msg)
            self.update_model(self.instance.pk, status=JobStatusChoices.FAILED, explanation=msg)
            return

        self.update_model(self.instance.pk, status=JobStatusChoices.SUCCESSFUL)
