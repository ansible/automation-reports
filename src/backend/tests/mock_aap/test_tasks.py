import pytest
import responses
import yaml
import logging

from backend.apps.aap_auth.models import BaseJWTUserToken
from backend.apps.common.models import Currency, FilterSet, Settings
from backend.apps.dispatch.tasks import _run_dispatch_startup_common
from backend.apps.scheduler.models import SyncJob, SyncSchedule, SyncScheduleState, JobTypeChoices as SyncJobTypeChoices
from backend.apps.scheduler.task_manager import SyncTaskManager
from backend.apps.scheduler.tasks import run_manager
from backend.apps.tasks.jobs import AAPParseDataTask, AAPSyncTask

from .fixtures import all_aap_versions, dict_sync_schedule_1min
from .fixtures import dict_cluster_26
from .fixtures import dict_cluster_25
from .fixtures import dict_cluster_24

from backend.apps.clusters.connector import ApiConnector
from backend.apps.clusters.models import AAPUser, ClusterSyncData, ClusterSyncStatus, ClusterVersionChoices, Cluster, Costs, ExecutionEnvironment, Host, InstanceGroup, Inventory, Job, JobHostSummary, JobLabel, JobStatusChoices, JobTemplate, Label, NameDescriptionModel, Organization, Project
from backend.apps.clusters.encryption import encrypt_value

from django.core.management import call_command

logger = logging.getLogger(__name__)

@pytest.mark.usefixtures("aap_api_responses")
# @pytest.mark.parametrize("aap_version_str", all_aap_versions)
@pytest.mark.parametrize("aap_version_str", ["2.6", "2.4"])
@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestDispatcherTask:
    def test_1(self, capsys, aap_version_str):
        aap_version_str_short = aap_version_str.replace(".", "")
        dict_cluster = eval(f"dict_cluster_{aap_version_str_short}")
        clusters_yaml_filename = f"/tmp/clusters-aap{aap_version_str_short}.yaml"

        with open(clusters_yaml_filename, "w") as fout:
            dict_clusters = dict(clusters=[
                dict(**dict_cluster, sync_schedules=[dict_sync_schedule_1min]),
            ])
            yaml.dump(dict_clusters, fout, indent=4)

        # initial state, of all models.
        assert 0 == Currency.objects.count()
        assert 0 == Settings.objects.count()
        assert 0 == FilterSet.objects.count()
        assert 0 == SyncSchedule.objects.count()
        assert 0 == SyncScheduleState.objects.count()
        assert 0 == SyncJob.objects.count() #
        assert 0 == Cluster.objects.count()
        assert 0 == ClusterSyncData.objects.count() #
        assert 0 == ClusterSyncStatus.objects.count() #
        assert 0 == Organization.objects.count() #
        assert 0 == JobTemplate.objects.count() #
        assert 0 == AAPUser.objects.count()
        assert 0 == Inventory.objects.count()
        assert 0 == ExecutionEnvironment.objects.count()
        assert 0 == InstanceGroup.objects.count()
        assert 0 == Label.objects.count()
        assert 0 == Host.objects.count()
        assert 0 == Project.objects.count()
        assert 0 == Job.objects.count()
        assert 0 == JobLabel.objects.count()
        assert 0 == JobHostSummary.objects.count()
        assert 0 == Costs.objects.count()

        call_command("setclusters", clusters_yaml_filename)
        assert 1 == Cluster.objects.count()
        assert 1 == SyncSchedule.objects.count()
        cluster = Cluster.objects.get()

        # call_command("run_dispatcher")
        # config = get_dispatcherd_config(for_service=True)
        # dispatcher_setup(config=config)
        # run_service() #
        
        # From config
        # backend.apps.dispatch.dispatcherd.DashboardTaskWorker - just pre-open DB connections
        # backend.apps.dispatch.tasks.dispatch_startup
        #      _run_dispatch_startup_common()
        #      redo_unfinished_tasks()

        # assert 0 == SyncSchedule.objects.count()
        # _run_dispatch_startup_common()

        schedule = SyncSchedule.objects.get()
        print(f"sync_schedule next_run={schedule.next_run}")

        assert 0 == SyncJob.objects.count()
        # SyncJob.signal_start
        # kdo ustvari sync job ?
        sync_kwargs = schedule.get_job_kwargs()
        sync_job = schedule.cluster.create_sync_job(**sync_kwargs)
        assert 1 == SyncJob.objects.count()
        
        sync_job.signal_start()
        # run_manager(SyncTaskManager)  # dispatcherd not configured
        manager = SyncTaskManager()
        # manager.schedule()
        # manager._schedule()

        # Create task corresponding to sync_job.
        task = AAPSyncTask()
        sync_job.status = JobStatusChoices.WAITING
        sync_job.save()

        # state before test
        assert 0 == Currency.objects.count()
        assert 0 == Settings.objects.count()
        assert 0 == FilterSet.objects.count()
        assert 1 == SyncSchedule.objects.count()
        assert 0 == SyncScheduleState.objects.count()
        assert 1 == SyncJob.objects.count()
        assert 1 == Cluster.objects.count()
        assert 0 == ClusterSyncData.objects.count()
        assert 0 == ClusterSyncStatus.objects.count()
        assert 0 == Organization.objects.count()
        assert 0 == JobTemplate.objects.count()
        assert 0 == AAPUser.objects.count()
        assert 0 == Inventory.objects.count()
        assert 0 == ExecutionEnvironment.objects.count()
        assert 0 == InstanceGroup.objects.count()
        assert 0 == Label.objects.count()
        assert 0 == Host.objects.count()
        assert 0 == Project.objects.count()
        assert 0 == Job.objects.count()
        assert 0 == JobLabel.objects.count()
        assert 0 == JobHostSummary.objects.count()
        assert 0 == Costs.objects.count()

        # the tested function
        task.run(pk=sync_job.pk)

        # state after test
        assert 0 == Currency.objects.count()
        assert 0 == Settings.objects.count()
        assert 0 == FilterSet.objects.count()
        assert 1 == SyncSchedule.objects.count()
        assert 0 == SyncScheduleState.objects.count()
        assert 1 == SyncJob.objects.filter(type=SyncJobTypeChoices.SYNC_JOBS).count()
        assert 4 == SyncJob.objects.filter(type=SyncJobTypeChoices.PARSE_JOB_DATA).count()
        assert 5 == SyncJob.objects.count()
        assert 1 == Cluster.objects.count()
        assert 4 == ClusterSyncData.objects.count() #
        assert 1 == ClusterSyncStatus.objects.count() #
        assert 2 == Organization.objects.count() #
        assert 3 == JobTemplate.objects.count() #
        assert 0 == AAPUser.objects.count()
        assert 0 == Inventory.objects.count()
        assert 0 == ExecutionEnvironment.objects.count()
        assert 0 == InstanceGroup.objects.count()
        assert 0 == Label.objects.count()
        assert 0 == Host.objects.count()
        assert 0 == Project.objects.count()
        assert 0 == Job.objects.count()
        assert 0 == JobLabel.objects.count()
        assert 0 == JobHostSummary.objects.count()
        assert 0 == Costs.objects.count()

        # Note: this seems to be ONLY the first step of sync.
        # Objects as AAPUser, Inventory etc - who creates those?
        # Answer - the ClusterSyncData.save creates SyncJob instances,
        # and SyncJob needs to be run by dispatherd.

    def test_2(self, capsys, aap_version_str):
        # This creates needed DB objects - SyncJob in particular.
        self.test_1(capsys, aap_version_str)
        call_command("dumpdata", "-o", "/tmp/test_1.yaml")

        assert 0 == Currency.objects.count()
        assert 0 == Settings.objects.count()
        assert 0 == FilterSet.objects.count()
        assert 1 == SyncSchedule.objects.count()
        assert 0 == SyncScheduleState.objects.count()
        assert 1 == SyncJob.objects.filter(type=SyncJobTypeChoices.SYNC_JOBS).count()
        assert 4 == SyncJob.objects.filter(type=SyncJobTypeChoices.PARSE_JOB_DATA).count()
        assert 5 == SyncJob.objects.count()
        assert 1 == Cluster.objects.count()
        assert 4 == ClusterSyncData.objects.count() #
        assert 1 == ClusterSyncStatus.objects.count() #
        assert 2 == Organization.objects.count() #
        assert 3 == JobTemplate.objects.count() #
        assert 0 == AAPUser.objects.count()
        assert 0 == Inventory.objects.count()
        assert 0 == ExecutionEnvironment.objects.count()
        assert 0 == InstanceGroup.objects.count()
        assert 0 == Label.objects.count()
        assert 0 == Host.objects.count()
        assert 0 == Project.objects.count()
        assert 0 == Job.objects.count()
        assert 0 == JobLabel.objects.count()
        assert 0 == JobHostSummary.objects.count()
        assert 0 == Costs.objects.count()

        # The first SyncJob (type=SyncJobTypeChoices.SYNC_JOBS) created
        # N ClusterSyncData and N SyncJob objects.
        # A ClusterSyncData contains one AAP json response.
        # A SyncJob(type=PARSE_JOB_DATA) will parse one ClusterSyncData.
        # We now test SyncJob parsing the ClusterSyncData.

        # state before test

        # the tested function
        if 1:
            sync_datas = [
                sd
                for sd in ClusterSyncData.objects.all()
                # if sd.data["url"] == "/api/controller/v2/jobs/13/"
                if sd.data["name"] == "jobtemplate2-org1"
            ]
            assert 2 == len(sync_datas)  # we run the jobtemplate2-org1 twice
            sync_data = sync_datas[0]
            # sync_data = ClusterSyncData.objects.all()[3]

            sync_job = SyncJob.objects.get(cluster_sync_data=sync_data)

            task = AAPParseDataTask()
            # sync_job.status = JobStatusChoices.WAITING
            sync_job.status = JobStatusChoices.RUNNING
            sync_job.save()
            task.instance = sync_job
            # task.instance = task.update_model(pk=sync_job.pk)
            # task.instance.status = JobStatusChoices.RUNNING
            # task.instance.status = JobStatusChoices.WAITING
            # task.instance.status = JobStatusChoices.NEW
            logger.warning(f"\n\n\nTTRT 11a ----------------------------------------------------------")
            task.run(pk=sync_job.pk)
            logger.warning(f"\n\n\nTTRT 22a task.instance.pk={task.instance.pk} sync_job.id={sync_job.id} ----------------------------------------------------------")

        # state after test - a single job was parsed
        assert 0 == Currency.objects.count()
        assert 0 == Settings.objects.count()
        assert 0 == FilterSet.objects.count()
        assert 1 == SyncSchedule.objects.count()
        assert 0 == SyncScheduleState.objects.count()
        assert 1 == SyncJob.objects.filter(type=SyncJobTypeChoices.SYNC_JOBS).count()
        assert 4 == SyncJob.objects.filter(type=SyncJobTypeChoices.PARSE_JOB_DATA).count()
        assert 5 == SyncJob.objects.count()
        assert 1 == Cluster.objects.count()
        assert 3 == ClusterSyncData.objects.count() #
        assert 1 == ClusterSyncStatus.objects.count()
        assert 2 == Organization.objects.count()
        assert 3 == JobTemplate.objects.count()
        assert 1 == AAPUser.objects.count() #
        assert 1 == Inventory.objects.count() #
        assert 1 == ExecutionEnvironment.objects.count() #
        assert 1 == InstanceGroup.objects.count()
        assert 1 == Label.objects.count()
        assert 1 == Host.objects.count() #
        assert 1 == Project.objects.count() #
        assert 1 == Job.objects.count() #
        assert 1 == JobLabel.objects.count()
        assert 1 == JobHostSummary.objects.count() #
        assert 0 == Costs.objects.count()

        if 1:
            for sync_data in ClusterSyncData.objects.all():
                logger.warning(f"\n\n\nTTRT 11b ----------------------------------------------------------")
                sync_job = SyncJob.objects.get(cluster_sync_data=sync_data)
                task = AAPParseDataTask()
                sync_job.status = JobStatusChoices.WAITING
                sync_job.save()

                # # state before test
                # the tested function
                task.run(pk=sync_job.pk)
                logger.warning(f"\n\n\nTTRT 22b ----------------------------------------------------------")

        # state after test - all jobs ware parsed
        assert 0 == Currency.objects.count()
        assert 0 == Settings.objects.count()
        assert 0 == FilterSet.objects.count()
        assert 1 == SyncSchedule.objects.count()
        assert 0 == SyncScheduleState.objects.count()
        assert 1 == SyncJob.objects.filter(type=SyncJobTypeChoices.SYNC_JOBS).count()
        assert 4 == SyncJob.objects.filter(type=SyncJobTypeChoices.PARSE_JOB_DATA).count()
        assert 5 == SyncJob.objects.count()
        assert 1 == Cluster.objects.count()
        assert 0 == ClusterSyncData.objects.count() #
        assert 1 == ClusterSyncStatus.objects.count()
        assert 2 == Organization.objects.count() #  TODO copy
        assert 3 == JobTemplate.objects.count() # TODO copy
        assert 1 == AAPUser.objects.count() # TODO create
        assert 1 == Inventory.objects.count() # TODO copy
        assert 1 == ExecutionEnvironment.objects.count() # TODO copy
        assert 1 == InstanceGroup.objects.count()
        assert 2 == Label.objects.count() # TODO create assign
        assert 1 == Host.objects.count() # TODO copy
        assert 2 == Project.objects.count() # TODO copy
        assert 4 == Job.objects.count() #
        assert 6 == JobLabel.objects.count()
        assert 4 == JobHostSummary.objects.count() #
        assert 0 == Costs.objects.count()
        # Here we see, which objects are missing in AAP, so that part of code is not tested.

# https://aap26.example.com:443/api/controller/v2/jobs/?page_size=100&page=1&order_by=finished&finished__gt=2025-10-23T13:01:09.768681Z
# https://aap26.example.com:443/api/controller/v2/jobs/?page_size=100&page=1&order_by=finished&finished__gt=2025-10-23T13:01:09.768681Z

# @task (queue=settings.DISPATCHER_PARSE_CHANNEL)
# class AAPParseDataTask(BaseTask):
# @task (queue=settings.DISPATCHER_SYNC_CHANNEL)
# class AAPSyncTask(BaseTask):
#
# @task (queue=settings.DISPATCHER_SYNC_CHANNEL)
# def sync_task_manager():


        # time.sleep(10)


# getclusters
# syncdata
        # job = SyncJob.objects.create(
        #     name=name,
        #     type=JobTypeChoices.SYNC_JOBS,
        #     launch_type=JobLaunchTypeChoices.MANUAL,
        #     cluster=cluster,
        #     job_args=job_args
        # )
        # job.signal_start()
