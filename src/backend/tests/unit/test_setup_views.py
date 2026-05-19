import json
from unittest import mock

import pytest
from rest_framework.test import APIClient, APIRequestFactory

from backend.api.v1.setup.serializers import ClusterSetupSerializer
from backend.apps.aap_auth.authentication import enforce_csrf


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
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestSetupViews:

    # ------------------------------------------------------------------
    # SetupStatusView  GET /api/v1/setup/status/
    # ------------------------------------------------------------------

    def test_setup_required_when_no_clusters(self, api_client):
        response = api_client.get('/api/v1/setup/status/')
        assert response.status_code == 200
        data = response.json()
        assert data == {'setup_required': True}

    def test_setup_not_required_when_cluster_exists(self, api_client, cluster):
        response = api_client.get('/api/v1/setup/status/')
        assert response.status_code == 200
        data = response.json()
        assert data == {'setup_required': False}

    # ------------------------------------------------------------------
    # enforce_csrf  (unit tests — no DB needed, but class marker is fine)
    # ------------------------------------------------------------------

    def test_enforce_csrf_safe_methods_exempt(self):
        factory = APIRequestFactory()
        for method_name in ('get', 'head', 'options'):
            request = getattr(factory, method_name)('/test/')
            request.COOKIES = {}
            request.META = {}
            # Must not raise for safe methods
            enforce_csrf(request)

    def test_enforce_csrf_raises_when_cookie_absent_on_post(self):
        from rest_framework.exceptions import PermissionDenied

        factory = APIRequestFactory()
        request = factory.post('/test/')
        request.COOKIES = {}
        request.META = {}

        with pytest.raises(PermissionDenied):
            enforce_csrf(request)

    def test_enforce_csrf_raises_on_token_mismatch(self):
        from rest_framework.exceptions import PermissionDenied

        factory = APIRequestFactory()
        request = factory.post('/test/')
        request.COOKIES = {'csrftoken': 'correct-token'}
        request.META['HTTP_X_XSRF_TOKEN'] = 'wrong-token'

        with pytest.raises(PermissionDenied):
            enforce_csrf(request)

    def test_enforce_csrf_passes_when_tokens_match(self):
        factory = APIRequestFactory()
        request = factory.post('/test/')
        request.COOKIES = {'csrftoken': 'matching-token'}
        request.META['HTTP_X_XSRF_TOKEN'] = 'matching-token'

        # Must not raise
        enforce_csrf(request)

    def test_enforce_csrf_accepts_x_csrf_token_header(self):
        factory = APIRequestFactory()
        request = factory.post('/test/')
        request.COOKIES = {'csrftoken': 'shared-token'}
        request.META['HTTP_X_CSRFTOKEN'] = 'shared-token'

        # Must not raise — Django-style header also accepted
        enforce_csrf(request)

    # ------------------------------------------------------------------
    # SetupLocalLoginView  POST /api/v1/setup/local_login/
    # ------------------------------------------------------------------

    def test_local_login_blocked_when_setup_complete(self, api_client, cluster):
        response = api_client.post(
            '/api/v1/setup/local_login/',
            data=json.dumps({'username': 'anyone', 'password': 'anything'}),
            content_type='application/json',
        )
        assert response.status_code == 403

    def test_local_login_rejects_wrong_password(self, api_client):
        from backend.apps.users.models import User

        User.objects.create_superuser(username='admin', password='correctpass')
        response = api_client.post(
            '/api/v1/setup/local_login/',
            data=json.dumps({'username': 'admin', 'password': 'wrongpass'}),
            content_type='application/json',
        )
        assert response.status_code == 401

    def test_local_login_succeeds_for_superuser(self, api_client):
        from backend.apps.users.models import User

        User.objects.create_superuser(username='admin', password='testpass')
        response = api_client.post(
            '/api/v1/setup/local_login/',
            data=json.dumps({'username': 'admin', 'password': 'testpass'}),
            content_type='application/json',
        )
        assert response.status_code == 204

    # ------------------------------------------------------------------
    # ClusterSetupSerializer
    # ------------------------------------------------------------------

    def test_cluster_write_serializer_valid_api_mode(self):
        data = {
            'protocol': 'https',
            'address': 'aap.example.com',
            'port': 443,
            'aap_version': 'AAP 2.5',
            'verify_ssl': True,
            'client_id': 'my-client-id',
            'client_secret': 'my-secret',
            'access_token': 'my-access-token',
            'refresh_token': 'my-refresh-token',
            'sync_mode': 'api',
        }
        serializer = ClusterSetupSerializer(data=data)
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
        serializer = ClusterSetupSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_cluster_write_serializer_client_id_optional(self):
        data = {
            'protocol': 'https',
            'address': 'aap.example.com',
            'port': 5432,
            'aap_version': 'AAP 2.4',
            'verify_ssl': True,
            'sync_mode': 'database',
            'db_host': 'db.example.com',
            'db_user': 'awx',
        }
        serializer = ClusterSetupSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['client_id'] == ''
