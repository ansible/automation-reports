import pytest
from unittest.mock import patch, MagicMock
from backend.apps.aap_auth.aap_auth import AAPAuth
from rest_framework.exceptions import AuthenticationFailed


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestAAPAuth:

    @pytest.mark.parametrize('expected', [
        {
            'name': 'test_name',
            'url': 'https://localhost/o/authorize',
            'client_id': 'test_client_id',
            'scope': 'read',
            'approval_prompt': 'auto',
            'response_type': 'code'
        }
    ])
    def test_ui_data_returns_expected_dict(self, expected):
        auth = AAPAuth()
        result = auth.ui_data()
        assert result == expected


    @patch("backend.apps.aap_auth.aap_auth.JWTToken")
    @patch("backend.apps.aap_auth.aap_auth.AAPAuth._aap_authorize")
    @patch("backend.apps.aap_auth.aap_auth.AAPAuth.get_user_data")
    def test_authorize_returns_tokens(self, mock_get_user_data, mock_aap_authorize, mock_jwt_token):
        mock_aap_token = MagicMock()
        mock_aap_authorize.return_value = mock_aap_token
        mock_user = MagicMock()
        mock_get_user_data.return_value = mock_user
        mock_jwt_instance = MagicMock()
        mock_jwt_token.return_value = mock_jwt_instance
        mock_jwt_instance.acquire_token_pair.return_value = {"access_token": "test_access", "refresh_token": "test_refresh"}
        auth = AAPAuth()
        result = auth.authorize(code="test_code", redirect_uri="http://test.com/callback")
        assert result["access_token"] == "test_access"
        assert result["refresh_token"] == "test_refresh"
        mock_aap_authorize.assert_called_once()
        mock_get_user_data.assert_called_once_with(mock_aap_token)
        mock_jwt_instance.acquire_token_pair.assert_called_once_with(aap_token=mock_aap_token, user=mock_user)

    @patch("backend.apps.aap_auth.aap_auth.AAPAuth._aap_authorize")
    @patch("backend.apps.aap_auth.aap_auth.AAPAuth.get_user_data")
    def test_authorize_aap_authorize_failure(self, mock_get_user_data, mock_aap_authorize):
        mock_aap_authorize.side_effect = AuthenticationFailed("Failed to obtain token")
        auth = AAPAuth()
        with pytest.raises(AuthenticationFailed, match="Failed to obtain token"):
            auth.authorize(code="test_code", redirect_uri="http://test.com/callback")

    @patch("backend.apps.aap_auth.aap_auth.AAPAuth._aap_authorize")
    @patch("backend.apps.aap_auth.aap_auth.AAPAuth.get_user_data")
    def test_authorize_get_user_data_failure(self, mock_get_user_data, mock_aap_authorize):
        mock_aap_token = MagicMock()
        mock_aap_authorize.return_value = mock_aap_token
        mock_get_user_data.side_effect = ValueError("Failed to fetch user data")
        auth = AAPAuth()
        with pytest.raises(ValueError, match="Failed to fetch user data"):
            auth.authorize(code="test_code", redirect_uri="http://test.com/callback")

    @patch("backend.apps.aap_auth.aap_auth.JwtUserToken.get_user_token")
    @patch("backend.apps.aap_auth.aap_auth.requests.post")
    def test_logout_revokes_token(self, mock_post, mock_get_user_token):
        mock_token = MagicMock()
        mock_token.id = 1
        mock_token.aap_token = "test_aap_token"
        mock_get_user_token.return_value = mock_token
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        auth = AAPAuth()
        result = auth.logout(access_token="test_access_token")
        assert result["success"] is True
        mock_get_user_token.assert_called_once_with("test_access_token")
        mock_post.assert_called_once_with(
            url=f"{auth.url}/o/revoke_token/",
            data={
                "client_id": auth.client_id,
                "client_secret": auth.client_secret,
                "token": "test_aap_token",
            },
            verify=False,
            allow_redirects=False,
            timeout=30,
        )
        mock_token.revoke_token.assert_called_once()
