import uuid
from datetime import datetime, timedelta
from typing import Dict

import jwt
import pytz

from backend.apps.aap_auth.models import JwtUserToken, JwtUserRefreshToken
from backend.apps.aap_auth.schema import AAPToken
from backend.apps.users.models import User
from django.conf import settings


class JWTToken:
    # Handles JWT token creation, decoding, and management

    def __init__(self):
        # Initialize token lifetimes and algorithm from settings
        self.access_token_lifetime_seconds = settings.JWT_ACCESS_TOKEN_LIFETIME_SECONDS
        self.refresh_token_lifetime_seconds = settings.JWT_REFRESH_TOKEN_LIFETIME_SECONDS
        self.now = datetime.now(pytz.utc)
        self.algorithm = 'HS256'

    @property
    def jti(self) -> str:
        # Generates a unique token identifier
        return uuid.uuid4().hex

    def _generate_token(self, payload: Dict[str, any], secret_key: str) -> str:
        # Encodes payload into a JWT using the secret key
        return jwt.encode(payload, secret_key, algorithm=self.algorithm)

    def get_payload(self, user: User, lifetime_seconds: int) -> Dict[str, any]:
        exp = self.now + timedelta(seconds=lifetime_seconds)
        return {
            'user_name': user.username,
            'iat': self.now,
            'exp': exp,
        }

    def acquire_token(self, user: User, aap_token: AAPToken) -> JwtUserToken:
        jti = self.jti
        payload = self.get_payload(user, self.access_token_lifetime_seconds)
        token = self._generate_token(payload=payload, secret_key=jti)
        user.log_login()
        return JwtUserToken.create_token(
            user=user,
            aap_token=aap_token,
            token=token,
            jti=jti,
            expires=payload['exp'],
        )

    def acquire_refresh_token(self, user: User, access_token: JwtUserToken) -> JwtUserRefreshToken:
        # Creates and stores a JWT refresh token for the user
        jti = self.jti
        payload = self.get_payload(user, self.refresh_token_lifetime_seconds)
        token = self._generate_token(payload=payload, secret_key=jti)
        return JwtUserRefreshToken.create_token(
            user=user,
            access_token=access_token,
            token=token,
            jti=jti,
            expires=payload['exp'],
        )

    def acquire_token_pair(self, user: User, aap_token: AAPToken) -> dict[str, JwtUserToken | JwtUserRefreshToken]:
        # Returns a dictionary with both access and refresh tokens
        access_token = self.acquire_token(user=user, aap_token=aap_token)
        refresh_token = self.acquire_refresh_token(user=user, access_token=access_token)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    def _decode(self, token: str, secret_key: str) -> Dict[str, any] | None:
        # Decodes a JWT and returns its payload, or None if invalid
        try:
            return jwt.decode(token, secret_key, [self.algorithm])
        except jwt.InvalidTokenError:
            return None

    def decode_token(self, token: str) -> JwtUserToken | None:
        # Validates and returns the access token object if valid
        db_token = JwtUserToken.get_user_token(token=token)
        if db_token is None or db_token.id is None:
            return None
        decoded_token = self._decode(token=token, secret_key=db_token.jti)
        return db_token if decoded_token else None

    def decode_refresh_token(self, token: str, access_token: str) -> JwtUserRefreshToken | None:
        # Validates and returns the refresh token object if valid and matches access token
        db_token = JwtUserRefreshToken.get_user_token(token=token)
        if db_token is None or db_token.id is None:
            return None
        decoded_token = self._decode(token=token, secret_key=db_token.jti)
        if decoded_token is None:
            return None
        return db_token if db_token.access_token.token == access_token else None
