from unittest.mock import patch, MagicMock

import jwt
import pytest

from backend.apps.aap_auth.jwt_token import JWTToken


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestJWTToken:

    def test_init_sets_lifetimes_and_algorithm(self):
        jwt_token = JWTToken()
        assert jwt_token.access_token_lifetime_seconds == 60
        assert jwt_token.refresh_token_lifetime_seconds == 7200
        assert jwt_token.algorithm == "HS256"

    def test_jti_is_unique(self):
        jwt_token = JWTToken()
        jti1 = jwt_token.jti
        jti2 = jwt_token.jti
        assert jti1 != jti2
        assert isinstance(jti1, str)
        assert isinstance(jti2, str)

    @patch("backend.apps.aap_auth.jwt_token.jwt.encode")
    def test_generate_token_encodes_payload(self, mock_encode):
        jwt_token = JWTToken()
        payload = {"foo": "bar"}
        secret = "secret"
        mock_encode.return_value = "encoded_token"
        result = jwt_token._generate_token(payload, secret)
        mock_encode.assert_called_once_with(payload, secret, algorithm="HS256")
        assert result == "encoded_token"

    def test_get_payload_returns_expected_fields(self):
        jwt_token = JWTToken()
        user = MagicMock()
        user.username = "test_user"
        payload = jwt_token.get_payload(user, 100, "test_jti")
        assert payload["sub"] == "test_user"
        assert payload["jti"] == "test_jti"
        assert "iat" in payload
        assert "exp" in payload

    @patch("backend.apps.aap_auth.jwt_token.JwtUserToken")
    def test_acquire_token_creates_token(self, mock_jut):
        jwt_token = JWTToken()
        user = MagicMock()
        aap_token = MagicMock()
        mock_jut.create_token.return_value = "token_obj"
        user.username = "test_user"
        user.log_login = MagicMock()
        jwt_token.acquire_token(user, aap_token)
        result = jwt_token.acquire_token(user, aap_token)
        assert result == "token_obj"

    @patch("backend.apps.aap_auth.jwt_token.JwtUserRefreshToken")
    @patch("backend.apps.aap_auth.jwt_token.JWTToken.get_payload")
    @patch("backend.apps.aap_auth.jwt_token.JWTToken._generate_token")
    def test_acquire_refresh_token_creates_refresh_token(self, mock_gen, mock_payload, mock_jurt):
        jwt_token = JWTToken()
        user = MagicMock()
        access_token = MagicMock()
        mock_payload.return_value = {"exp": "expiry"}
        mock_gen.return_value = "refresh_token"
        mock_jurt.create_token.return_value = "refresh_token_obj"
        result = jwt_token.acquire_refresh_token(user, access_token)
        mock_jurt.create_token.assert_called_once()
        assert result == "refresh_token_obj"

    @patch("backend.apps.aap_auth.jwt_token.JWTToken.acquire_token")
    @patch("backend.apps.aap_auth.jwt_token.JWTToken.acquire_refresh_token")
    def test_acquire_token_pair_returns_both_tokens(self, mock_refresh, mock_access):
        jwt_token = JWTToken()
        user = MagicMock()
        aap_token = MagicMock()
        mock_access.return_value = "access"
        mock_refresh.return_value = "refresh"
        result = jwt_token.acquire_token_pair(user, aap_token)
        assert result["access_token"] == "access"
        assert result["refresh_token"] == "refresh"

    @patch("backend.apps.aap_auth.jwt_token.jwt.decode")
    def test_decode_valid_token_returns_payload(self, mock_decode):
        jwt_token = JWTToken()
        mock_decode.return_value = {"foo": "bar"}
        result = jwt_token._decode("token", "secret")
        assert result == {"foo": "bar"}

    @patch("backend.apps.aap_auth.jwt_token.jwt.decode")
    def test_decode_invalid_token_returns_none(self, mock_decode):
        jwt_token = JWTToken()
        mock_decode.side_effect = jwt.InvalidTokenError
        result = jwt_token._decode("token", "secret")
        assert result is None

    @patch("backend.apps.aap_auth.jwt_token.JwtUserToken.get_user_token")
    @patch("backend.apps.aap_auth.jwt_token.JWTToken._decode")
    def test_decode_token_valid(self, mock_decode, mock_get_token):
        jwt_token = JWTToken()
        db_token = MagicMock()
        db_token.id = 1
        mock_get_token.return_value = db_token
        mock_decode.return_value = {"foo": "bar"}
        result = jwt_token.decode_token("token")
        assert result == db_token

    @patch("backend.apps.aap_auth.jwt_token.JwtUserToken.get_user_token")
    def test_decode_token_invalid(self, mock_get_token):
        jwt_token = JWTToken()
        mock_get_token.return_value = None
        result = jwt_token.decode_token("token")
        assert result is None

    @patch("backend.apps.aap_auth.jwt_token.JwtUserRefreshToken.get_user_token")
    @patch("backend.apps.aap_auth.jwt_token.JWTToken._decode")
    def test_decode_refresh_token_valid(self, mock_decode, mock_get_token):
        jwt_token = JWTToken()
        db_token = MagicMock()
        db_token.id = 1
        db_token.access_token.token = "access"
        mock_get_token.return_value = db_token
        mock_decode.return_value = {"foo": "bar"}
        result = jwt_token.decode_refresh_token("token", "access")
        assert result == db_token

    @patch("backend.apps.aap_auth.jwt_token.JwtUserRefreshToken.get_user_token")
    @patch("backend.apps.aap_auth.jwt_token.JWTToken._decode")
    def test_decode_refresh_token_invalid_access(self, mock_decode, mock_get_token):
        jwt_token = JWTToken()
        db_token = MagicMock()
        db_token.id = 1
        db_token.access_token.token = "other"
        mock_get_token.return_value = db_token
        mock_decode.return_value = {"foo": "bar"}
        result = jwt_token.decode_refresh_token("token", "access")
        assert result is None

    @patch("backend.apps.aap_auth.jwt_token.JwtUserRefreshToken.get_user_token")
    @patch("backend.apps.aap_auth.jwt_token.JWTToken._decode")
    def test_decode_refresh_token_invalid_token(self, mock_decode, mock_get_token):
        jwt_token = JWTToken()
        db_token = MagicMock()
        db_token.id = 1
        mock_get_token.return_value = db_token
        mock_decode.return_value = None
        result = jwt_token.decode_refresh_token("token", "access")
        assert result is None
