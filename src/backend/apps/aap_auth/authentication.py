import logging

from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, CSRFCheck
from rest_framework.request import Request

from backend.apps.aap_auth.jwt_token import JWTToken

logger = logging.getLogger("automation-dashboard.auth")


def enforce_csrf(request):
    """
    Enforce CSRF validation.
    """
    logger.info("Starting CSRF validation.")
    check = CSRFCheck(request)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        logger.error('CSRF Failed: %s' % reason)
        raise exceptions.PermissionDenied('CSRF Failed: %s' % reason)


class AAPAuthentication(BaseAuthentication):
    def authenticate(self, request: Request):
        logger.info("Starting authentication process")
        token = request.COOKIES.get(settings.AUTH_COOKIE_ACCESS_TOKEN_NAME) or None
        logger.debug(f"Token from cookies: {token}")

        if token is None:
            logger.info("No token found in cookies")
            return None

        if len(token) < 10:
            logger.warning("Token length is too short")
            return None

        logger.debug("Attempting to decode token")
        jwt_token = JWTToken()
        db_token = jwt_token.decode_token(token)

        if db_token is None:
            logger.warning("Failed to decode token")
            return None

        if not db_token.user.is_active:
            logger.warning("User is not active")
            return None

        enforce_csrf(request)
        logger.info("Authentication successful")
        return db_token.user, token

    def authenticate_header(self, request: Request) -> str:
        logger.debug("Returning authentication header")
        return "Bearer"
