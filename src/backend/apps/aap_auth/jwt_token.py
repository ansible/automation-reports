import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict

import jwt
import pytz
from django.conf import settings

from backend.apps.aap_auth.models import JwtUserToken, JwtUserRefreshToken
from backend.apps.aap_auth.schema import AAPToken
from backend.apps.users.models import User

logger = logging.getLogger("automation-dashboard.jwt")


class JWTToken:
    # Handles JWT token creation, decoding, and management

    def __init__(self):
        logger.info("Initializing JWTToken")
        self.access_token_lifetime_seconds = settings.JWT_ACCESS_TOKEN_LIFETIME_SECONDS
        self.refresh_token_lifetime_seconds = settings.JWT_REFRESH_TOKEN_LIFETIME_SECONDS
        self.now = datetime.now(pytz.utc)
        self.algorithm = 'HS256'
        logger.debug(f"Access token lifetime: {self.access_token_lifetime_seconds}, "
                     f"Refresh token lifetime: {self.refresh_token_lifetime_seconds}, "
                     f"Algorithm: {self.algorithm}")

    @property
    def jti(self) -> str:
        jti = uuid.uuid4().hex
        logger.debug(f"Generated JTI: {jti}")
        return jti

    def _generate_token(self, payload: Dict[str, any], secret_key: str) -> str:
        logger.debug(f"Generating token with payload: {payload}")
        return jwt.encode(payload, secret_key, algorithm=self.algorithm)

    def get_payload(self, user: User, lifetime_seconds: int, jti: str) -> Dict[str, any]:
        exp = self.now + timedelta(seconds=lifetime_seconds)
        logger.debug(f"Creating payload for user: {user.username}, exp: {exp}, jti: {jti}")
        return {
            'sub': user.username,
            'iat': self.now,
            'exp': exp,
            'jti': jti,
        }

    def acquire_token(self, user: User, aap_token: AAPToken) -> JwtUserToken:
        logger.info(f"Acquiring access token for user: {user.username}")
        jti = self.jti
        payload = self.get_payload(user, self.access_token_lifetime_seconds, jti)
        token = self._generate_token(payload=payload, secret_key=jti)
        user.log_login()
        logger.debug(f"Access token generated for user: {user.username}, jti: {jti}")
        return JwtUserToken.create_token(
            user=user,
            aap_token=aap_token,
            token=token,
            jti=jti,
            expires=payload['exp'],
        )

    def acquire_refresh_token(self, user: User, access_token: JwtUserToken) -> JwtUserRefreshToken:
        logger.info(f"Acquiring refresh token for user: {user.username}")
        jti = self.jti
        payload = self.get_payload(user, self.refresh_token_lifetime_seconds, jti)
        token = self._generate_token(payload=payload, secret_key=jti)
        logger.debug(f"Refresh token generated for user: {user.username}, jti: {jti}")
        return JwtUserRefreshToken.create_token(
            user=user,
            access_token=access_token,
            token=token,
            jti=jti,
            expires=payload['exp'],
        )

    def acquire_token_pair(self, user: User, aap_token: AAPToken) -> dict[str, JwtUserToken | JwtUserRefreshToken]:
        logger.info(f"Acquiring token pair for user: {user.username}")
        access_token = self.acquire_token(user=user, aap_token=aap_token)
        refresh_token = self.acquire_refresh_token(user=user, access_token=access_token)
        logger.debug(f"Token pair acquired for user: {user.username}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    def _decode(self, token: str, secret_key: str) -> Dict[str, any] | None:
        logger.debug(f"Decoding token.")
        try:
            return jwt.decode(token, secret_key, [self.algorithm])
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token error: {e}")
            return None

    def decode_token(self, token: str) -> JwtUserToken | None:
        logger.info("Decoding access token")
        db_token = JwtUserToken.get_user_token(token=token)
        if db_token is None or db_token.id is None:
            logger.warning("Access token not found or invalid")
            return None
        decoded_token = self._decode(token=token, secret_key=db_token.jti)
        if decoded_token:
            logger.debug("Access token decoded successfully")
            return db_token
        else:
            logger.warning("Failed to decode access token")
            return None

    def decode_refresh_token(self, token: str) -> JwtUserRefreshToken | None:
        logger.info("Decoding refresh token")
        db_token = JwtUserRefreshToken.get_user_token(token=token)
        if db_token is None or db_token.id is None:
            logger.warning("Refresh token not found or invalid")
            return None
        decoded_token = self._decode(token=token, secret_key=db_token.jti)
        if decoded_token is None:
            logger.warning("Failed to decode refresh token")
            return None
        logger.debug("Refresh token decoded successfully")
        return db_token
