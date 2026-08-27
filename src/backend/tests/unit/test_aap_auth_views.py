from unittest.mock import patch, MagicMock
import pytest
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import AuthenticationFailed

from backend.api.v1.aap_auth.views import AAPTokenView


@pytest.mark.django_db
class TestAAPTokenView:
    """Test AAPTokenView with PKCE support."""

    @patch("backend.api.v1.aap_auth.views.AAPAuth")
    def test_post_without_code_verifier(self, mock_aap_auth_class):
        mock_aap_auth = MagicMock()
        mock_aap_auth_class.return_value = mock_aap_auth
        mock_tokens = {
            "access_token": MagicMock(token="test_access", expires="2099-01-01"),
            "refresh_token": MagicMock(token="test_refresh", expires="2099-01-01"),
        }
        mock_aap_auth.authorize.return_value = mock_tokens

        factory = APIRequestFactory()
        request = factory.post(
            "/api/v1/aap_auth/token/",
            {"auth_code": "test_code", "redirect_uri": "http://test.com/callback"},
            format="json"
        )

        view = AAPTokenView.as_view()
        response = view(request)

        assert response.status_code == 204
        mock_aap_auth.authorize.assert_called_once_with("test_code", "http://test.com/callback", None)

    @patch("backend.api.v1.aap_auth.views.AAPAuth")
    def test_post_with_code_verifier(self, mock_aap_auth_class):
        mock_aap_auth = MagicMock()
        mock_aap_auth_class.return_value = mock_aap_auth
        mock_tokens = {
            "access_token": MagicMock(token="test_access", expires="2099-01-01"),
            "refresh_token": MagicMock(token="test_refresh", expires="2099-01-01"),
        }
        mock_aap_auth.authorize.return_value = mock_tokens

        factory = APIRequestFactory()
        code_verifier = "test_pkce_verifier_value"
        request = factory.post(
            "/api/v1/aap_auth/token/",
            {
                "auth_code": "test_code",
                "redirect_uri": "http://test.com/callback",
                "code_verifier": code_verifier,
            },
            format="json"
        )

        view = AAPTokenView.as_view()
        response = view(request)

        assert response.status_code == 204
        mock_aap_auth.authorize.assert_called_once_with("test_code", "http://test.com/callback", code_verifier)

    @patch("backend.api.v1.aap_auth.views.AAPAuth")
    def test_post_missing_auth_code(self, mock_aap_auth_class):
        factory = APIRequestFactory()
        request = factory.post(
            "/api/v1/aap_auth/token/",
            {"redirect_uri": "http://test.com/callback"},
            format="json"
        )

        view = AAPTokenView.as_view()
        response = view(request)

        assert response.status_code == 401

    @patch("backend.api.v1.aap_auth.views.AAPAuth")
    def test_post_missing_redirect_uri(self, mock_aap_auth_class):
        factory = APIRequestFactory()
        request = factory.post(
            "/api/v1/aap_auth/token/",
            {"auth_code": "test_code"},
            format="json"
        )

        view = AAPTokenView.as_view()
        response = view(request)

        assert response.status_code == 401
