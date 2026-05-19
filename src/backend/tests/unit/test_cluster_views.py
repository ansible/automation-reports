import json
from unittest import mock

import pytest
from rest_framework.test import APIClient

from backend.api.v1.clusters.serializers import ClusterReadSerializer, ClusterWriteSerializer
from backend.apps.clusters.encryption import encrypt_value
from backend.apps.clusters.models import Cluster


# ---------------------------------------------------------------------------
# Local fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def mock_aap_auth(superuser):
    with mock.patch("backend.apps.aap_auth.authentication.AAPAuthentication.authenticate") as m:
        m.return_value = superuser, None
        yield m


# ---------------------------------------------------------------------------
# Minimal valid cluster payload (api mode, no token fields required)
# ---------------------------------------------------------------------------

_CLUSTER_PAYLOAD = {
    'protocol': 'https',
    'address': 'aap.example.com',
    'port': 443,
    'aap_version': 'AAP 2.5',
    'verify_ssl': True,
    'sync_mode': 'api',
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestClusterViews:

    # ------------------------------------------------------------------
    # ClusterListCreateView  GET /api/v1/clusters/
    # ------------------------------------------------------------------

    def test_list_clusters_empty(self, mock_aap_auth, api_client):
        response = api_client.get('/api/v1/clusters/')
        assert response.status_code == 200
        assert response.json() == []

    def test_list_clusters_returns_clusters(self, mock_aap_auth, api_client, cluster):
        response = api_client.get('/api/v1/clusters/')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['address'] == 'localhost'

    # ------------------------------------------------------------------
    # ClusterListCreateView  POST /api/v1/clusters/
    # ------------------------------------------------------------------

    def test_create_cluster_api_mode(self, mock_aap_auth, api_client):
        response = api_client.post(
            '/api/v1/clusters/',
            data=json.dumps(_CLUSTER_PAYLOAD),
            content_type='application/json',
        )
        assert response.status_code == 201
        # Verify the cluster was actually stored in the database
        assert Cluster.objects.filter(address='aap.example.com').exists()

    def test_create_cluster_empty_tokens_stored_as_empty_bytes(self, mock_aap_auth, api_client):
        """When no token fields are supplied the model fields should be stored as b''."""
        api_client.post(
            '/api/v1/clusters/',
            data=json.dumps(_CLUSTER_PAYLOAD),
            content_type='application/json',
        )
        cluster = Cluster.objects.get(address='aap.example.com')
        assert bytes(cluster.access_token) == b''
        assert bytes(cluster.refresh_token) == b''

    def test_create_cluster_has_access_token_false_when_no_token(self, mock_aap_auth, api_client):
        response = api_client.post(
            '/api/v1/clusters/',
            data=json.dumps(_CLUSTER_PAYLOAD),
            content_type='application/json',
        )
        assert response.status_code == 201
        data = response.json()
        assert data['has_access_token'] is False

    # ------------------------------------------------------------------
    # ClusterReadSerializer.get_has_access_token  (unit tests)
    # ------------------------------------------------------------------

    def test_has_access_token_false_for_empty_bytes(self, cluster):
        # Override access_token to empty bytes without re-saving to DB
        cluster.access_token = b''
        serializer = ClusterReadSerializer(cluster)
        assert serializer.data['has_access_token'] is False

    def test_has_access_token_true_for_nonempty(self, cluster):
        # cluster fixture stores a real encrypted non-empty token
        serializer = ClusterReadSerializer(cluster)
        assert serializer.data['has_access_token'] is True

    # ------------------------------------------------------------------
    # ClusterWriteSerializer validation
    # ------------------------------------------------------------------

    def test_cluster_write_serializer_valid_api_mode(self):
        serializer = ClusterWriteSerializer(data=_CLUSTER_PAYLOAD)
        assert serializer.is_valid(), serializer.errors

    def test_cluster_write_serializer_valid_database_mode(self):
        data = {
            'protocol': 'https',
            'address': 'aap.example.com',
            'port': 443,
            'aap_version': 'AAP 2.6',
            'verify_ssl': False,
            'sync_mode': 'database',
            'db_host': 'db.example.com',
            'db_port': 5432,
            'db_name': 'awx',
            'db_user': 'awx',
            'db_password': 'secret',
        }
        serializer = ClusterWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
