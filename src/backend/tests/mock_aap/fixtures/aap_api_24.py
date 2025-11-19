import pytest
import responses

from backend.apps.clusters.models import Cluster
from backend.apps.clusters.encryption import encrypt_value


dict_cluster_24 = dict(
    protocol="https",
    address="aap24.example.com",
    port=8443,
    access_token="access-token-24",
    refresh_token="refresh-token-24",
    client_id="client-id-24",
    client_secret="client-secret-24",
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
