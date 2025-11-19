import pytest
import responses

from backend.apps.clusters.models import Cluster
from backend.apps.clusters.encryption import encrypt_value


dict_cluster_25 = dict(
    protocol="https",
    address="aap25.example.com",
    port=443,
    access_token="access-token-25",
    refresh_token="refresh-token-25",
    client_id="client-id-25",
    client_secret="client-secret-25",
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
def aap_api_responses_25():
    responses.add(
        responses.GET,
        "https://aap25.example.com:443/api/gateway/v1/ping/",
        json={"version":"2.5","pong":"2025-11-19 09:38:32.398165","status":"good","db_connected":True,"proxy_connected":True},
        status=200,
        content_type='application/json'
    )
