import pytest
import responses
import yaml

from .fixtures import all_aap_versions, dict_sync_schedule_1min
from .fixtures import dict_cluster_26
from .fixtures import dict_cluster_25
from .fixtures import dict_cluster_24

from backend.apps.clusters.connector import ApiConnector
from backend.apps.clusters.models import ClusterVersionChoices, Cluster
from backend.apps.clusters.encryption import encrypt_value

from django.core.management import call_command


@pytest.mark.usefixtures("aap_api_responses")
@pytest.mark.parametrize("aap_version_str", all_aap_versions)
@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestSetClusters:
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

        call_command("setclusters", clusters_yaml_filename)

        captured = capsys.readouterr()
        assert f"Adding cluster: address=aap{aap_version_str_short}.example.com\n" in captured.out
        assert "Successfully set up AAP clusters\n" in captured.out
        assert 1 == Cluster.objects.count()
        cluster = Cluster.objects.get()
        assert cluster.port == int(dict_cluster["port"])
        assert cluster.base_url == f"https://aap{aap_version_str_short}.example.com:{cluster.port}"
