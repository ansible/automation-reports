import pytest
import responses

from backend.apps.clusters.connector import ApiConnector
from backend.apps.clusters.models import ClusterVersionChoices, Cluster
from backend.apps.clusters.encryption import encrypt_value


@pytest.fixture
def cluster_26():
    """Creates temporary data."""
    Cluster.objects.create(
        protocol="https",
        address="aap26.example.com",
        port=443,
        access_token=encrypt_value(b"access-token-26"),
        refresh_token=encrypt_value(b"refresh-token-26"),
        client_id="client-id-26",
        client_secret=encrypt_value(b"client-secret-26"),
        verify_ssl=True,
    )


@pytest.fixture
def cluster_25():
    """Creates temporary data."""
    Cluster.objects.create(
        protocol="https",
        address="aap25.example.com",
        port=443,
        access_token=encrypt_value(b"access-token-25"),
        refresh_token=encrypt_value(b"refresh-token-25"),
        client_id="client-id-25",
        client_secret=encrypt_value(b"client-secret-25"),
        verify_ssl=True,
    )


@pytest.fixture
def cluster_24():
    """Creates temporary data."""
    Cluster.objects.create(
        protocol="https",
        address="aap24.example.com",
        port=8443,
        access_token=encrypt_value(b"access-token-24"),
        refresh_token=encrypt_value(b"refresh-token-24"),
        client_id="client-id-24",
        client_secret=encrypt_value(b"client-secret-24"),
        verify_ssl=True,
    )


@pytest.fixture
def aap_api_responses_26():
    responses.add(
        responses.GET,
        "https://aap26.example.com:443/api/gateway/v1/ping/",
        json={"status":"good","version":"2.6","pong":"2025-11-19 08:19:48.890695","db_connected":True,"proxy_connected":True},
        status=200,
        content_type='application/json'
    )


@pytest.fixture
def aap_api_responses_25():
    responses.add(
        responses.GET,
        "https://aap25.example.com:443/api/gateway/v1/ping/",
        json={"version":"2.5","pong":"2025-11-19 09:38:32.398165","status":"good","db_connected":True,"proxy_connected":True},
        status=200,
        content_type='application/json'
    )


@pytest.fixture
def aap_api_responses_24():
    responses.add(
        responses.GET,
        "https://aap24.example.com:8443/api/gateway/v1/ping/",
        json={"detail":"The requested resource could not be found."},
        status=404,
        content_type='application/json'
    )
    responses.add(
        responses.GET,
        "https://aap24.example.com:8443/api/v2/ping/",
        json={"ha":False,"version":"4.5.15","active_node":"rh-savings-aap24.novalocal","install_uuid":"4994da8f-a38f-4610-a6c3-ef410cbd2e2e","instances":[{"node":"rh-savings-aap24.novalocal","node_type":"hybrid","uuid":"eba627ff-78dd-4aaa-8b46-6e539880b808","heartbeat":"2025-11-19T09:40:51.214112Z","capacity":136,"version":"4.5.15"}],"instance_groups":[{"name":"controlplane","capacity":136,"instances":["rh-savings-aap24.novalocal"]},{"name":"default","capacity":136,"instances":["rh-savings-aap24.novalocal"]}]},
        status=200,
        content_type='application/json'
    )


# How to "combine" smaller fixtures - syntax sugar
# https://smarie.github.io/python-pytest-cases/pytest_goodies/#unpack_fixture-unpack_into

@pytest.mark.django_db(transaction=True, reset_sequences=True)
@pytest.mark.usefixtures("cluster_26", "aap_api_responses_26")
class TestApiConnector_for_v26_only:
    def test_detect_aap_version(self):
        cluster = Cluster.objects.get(address="aap26.example.com")
        apiconn = ApiConnector(cluster)
        aap_version = apiconn.detect_aap_version()
        assert aap_version == ClusterVersionChoices.AAP26


all_aap_versions = ["2.6", "2.5", "2.4"]


@pytest.fixture
def aap_fixtures(request):
    aap_version_str = request.param
    aap_version_str_short = aap_version_str.replace(".", "")
    assert aap_version_str in all_aap_versions

    cluster = request.getfixturevalue("cluster_" + aap_version_str_short)
    api_reponses = request.getfixturevalue("aap_api_responses_" + aap_version_str_short)
    return aap_version_str, cluster, api_reponses


@pytest.mark.parametrize("aap_fixtures", all_aap_versions, indirect=True)
@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestApiConnector:
    def test_detect_aap_version(self, aap_fixtures):
        aap_version_str = aap_fixtures[0]
        expected_aap_version = "AAP " + aap_version_str
        address = "aap" + aap_version_str.replace(".", "") + ".example.com"

        cluster = Cluster.objects.get(address=address)
        apiconn = ApiConnector(cluster)
        aap_version = apiconn.detect_aap_version()
        assert aap_version in ClusterVersionChoices.values
        assert aap_version == expected_aap_version
