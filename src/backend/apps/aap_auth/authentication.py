import logging

from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, CSRFCheck
from rest_framework.request import Request

from backend.apps.aap_auth.jwt_token import JWTToken

logger = logging.getLogger("automation_dashboard.auth")


_CSRF_SAFE_METHODS = frozenset({'GET', 'HEAD', 'OPTIONS', 'TRACE'})


def enforce_csrf(request):
    """
    Enforce CSRF validation using the double-submit cookie pattern.

    Safe methods (GET, HEAD, OPTIONS, TRACE) are exempt.  For all other methods
    the csrftoken cookie must be present and must match the token sent in either
    X-CSRFToken (Django default) or X-XSRF-TOKEN (axios default).

    Silently skipping validation when the cookie is absent would allow any
    unauthenticated cross-site request to bypass CSRF entirely, so we treat a
    missing cookie as a hard failure for state-changing methods.
    """
    logger.info("Starting CSRF validation.")

    if request.method in _CSRF_SAFE_METHODS:
        return

    cookie_token = request.COOKIES.get('csrftoken', '')
    if not cookie_token:
        logger.error('CSRF Failed: csrftoken cookie is absent')
        raise exceptions.PermissionDenied('CSRF Failed: missing CSRF cookie')

    header_token = (
        request.META.get('HTTP_X_XSRF_TOKEN', '')
        or request.META.get('HTTP_X_CSRFTOKEN', '')
    )

    if not header_token or header_token != cookie_token:
        logger.error('CSRF Failed: token mismatch or missing header')
        raise exceptions.PermissionDenied('CSRF Failed: token mismatch')


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
