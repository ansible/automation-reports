import json
import pytest
import responses
import yaml
import os
from django.conf import settings

from .fixtures import all_aap_versions, dict_sync_schedule_1min, dict_sync_schedule_10sec
from backend.apps.clusters.models import AAPUser, ClusterSyncData, ClusterSyncStatus, Cluster, Costs, ExecutionEnvironment, Host, InstanceGroup, Inventory, Job, JobHostSummary, JobLabel, JobTemplate, Label, Organization, Project
from backend.apps.common.models import Currency, FilterSet, Settings
from backend.apps.scheduler.models import SyncJob, SyncSchedule, SyncScheduleState, JobTypeChoices as SyncJobTypeChoices

from django.core.management import call_command
import subprocess
import time

@pytest.mark.skipif(
    os.environ.get('RUN_REAL_AAP_TESTS', '0') != '1',
    reason="Skipping full test. Set RUN_REAL_AAP_TESTS=1 environment variable to run."
)
#@pytest.mark.parametrize("aap_version_str", all_aap_versions)
@pytest.mark.parametrize("aap_version_str", ["2.6"])
@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestSetClusters:
    def test_1(self, aap_version_str):
        aap_version_str_short = aap_version_str.replace(".", "")

        # use aap-dev for local testing
        with open("tests/mock_aap/aap_access.json", "r") as ff:
            aap_access = json.load(ff)
        aap_address = aap_access['aap_address']
        aap_url = f"{aap_access['aap_protocol']}://{aap_access['aap_address']}:{aap_access['aap_port']}"
        dict_cluster = dict(
            protocol=aap_access["aap_protocol"],
            address=aap_access["aap_address"],
            port=int(aap_access["aap_port"]),
            access_token=aap_access["access_token"],
            refresh_token=aap_access["refresh_token"],
            client_id=aap_access["client_id"],
            client_secret=aap_access["client_secret"],
            verify_ssl=True,
        )
        clusters_yaml_filename = f"/tmp/clusters-aap{aap_version_str_short}.yaml"
        with open(clusters_yaml_filename, "w") as fout:
            dict_clusters = dict(clusters=[
                dict(**dict_cluster, sync_schedules=[dict_sync_schedule_10sec]),
            ])
            yaml.dump(dict_clusters, fout, indent=4)

        assert 0 == Cluster.objects.count()
        responses.add_passthru(aap_url)

        call_command("setclusters", clusters_yaml_filename)
        call_command("syncdata", "--since=2026-01-01", "--until=2036-01-01")
        assert 1 == Cluster.objects.count()
        cluster = Cluster.objects.get()
        assert cluster.port == int(dict_cluster["port"])
        assert cluster.base_url == aap_url

        # Start the dispatcher in the background
        env = os.environ.copy()
        env['DJANGO_SETTINGS_MODULE'] = 'backend.tests.settings_for_test'
        # Use the TEST database configuration
        test_db_name = settings.DATABASES['TEST']['NAME']
        env['DB_NAME'] = test_db_name
        dispather_proc = subprocess.Popen(["python", "manage.py", "run_dispatcher"], env=env)
        time.sleep(60)  # wait for first sync
        dispather_proc.send_signal(subprocess.signal.SIGTERM)
        dispather_proc.wait(timeout=10)

        # state after test - all jobs were parsed
        assert 5 == Currency.objects.count()
        assert 1 == Settings.objects.count()
        assert 0 == FilterSet.objects.count()
        assert 1 == SyncSchedule.objects.count()
        assert 1 == SyncScheduleState.objects.count()
        assert 2 == SyncJob.objects.filter(type=SyncJobTypeChoices.SYNC_JOBS).count()
        assert 4 == SyncJob.objects.filter(type=SyncJobTypeChoices.PARSE_JOB_DATA).count()
        assert 6 == SyncJob.objects.count()
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
