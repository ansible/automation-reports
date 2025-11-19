import pytest
import responses

from backend.apps.clusters.models import Cluster
from backend.apps.clusters.encryption import encrypt_value


dict_cluster_26 = dict(
    protocol="https",
    address="aap26.example.com",
    port=443,
    access_token="access-token-26",
    refresh_token="refresh-token-26",
    client_id="client-id-26",
    client_secret="client-secret-26",
    verify_ssl=True,
)


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
def aap_api_responses_26():
    responses.add(
        responses.GET,
        "https://aap26.example.com:443/api/gateway/v1/ping/",
        json={"status":"good","version":"2.6","pong":"2025-11-19 08:19:48.890695","db_connected":True,"proxy_connected":True},
        status=200,
        content_type='application/json'
    )

