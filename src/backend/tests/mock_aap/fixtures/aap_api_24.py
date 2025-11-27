import pytest
import responses

from backend.apps.clusters.models import Cluster
from backend.apps.clusters.encryption import encrypt_value
from .aap_common import aap_api_responses_versioned


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
    return aap_api_responses_versioned("24")
