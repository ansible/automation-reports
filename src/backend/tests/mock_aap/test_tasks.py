import time
import pytest
import responses
import yaml

from backend.apps.dispatch.tasks import _run_dispatch_startup_common
from backend.apps.scheduler.models import SyncJob, SyncSchedule
from backend.apps.scheduler.task_manager import SyncTaskManager
from backend.apps.scheduler.tasks import run_manager
from backend.apps.tasks.jobs import AAPSyncTask

from .fixtures import all_aap_versions, dict_sync_schedule_1min
from .fixtures import dict_cluster_26
from .fixtures import dict_cluster_25
from .fixtures import dict_cluster_24

from backend.apps.clusters.connector import ApiConnector
from backend.apps.clusters.models import ClusterSyncData, ClusterVersionChoices, Cluster, JobStatusChoices
from backend.apps.clusters.encryption import encrypt_value

from django.core.management import call_command


@pytest.mark.usefixtures("aap_api_responses")
# @pytest.mark.parametrize("aap_version_str", all_aap_versions)
@pytest.mark.parametrize("aap_version_str", ["2.6"])
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

        assert 0 == Cluster.objects.count()
        assert 0 == SyncSchedule.objects.count()
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

        assert 1 == SyncSchedule.objects.count()
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

        # task <- sync_job
        task = AAPSyncTask()
        sync_job.status = JobStatusChoices.WAITING
        sync_job.save()
        task.run(pk=sync_job.pk)

        assert 0


# @task (queue=settings.DISPATCHER_PARSE_CHANNEL)
# class AAPParseDataTask(BaseTask):
# @task (queue=settings.DISPATCHER_SYNC_CHANNEL)
# class AAPSyncTask(BaseTask):
#
# @task (queue=settings.DISPATCHER_SYNC_CHANNEL)
# def sync_task_manager():

        ClusterSyncData.save

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
