import logging

from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, CSRFCheck
from rest_framework.request import Request

from backend.apps.aap_auth.jwt_token import JWTToken

logger = logging.getLogger("automation-dashboard")


def enforce_csrf(request):
    """
    Enforce CSRF validation.
    """
    check = CSRFCheck(request)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise exceptions.PermissionDenied('CSRF Failed: %s' % reason)


class AAPAuthentication(BaseAuthentication):
    def authenticate(self, request: Request):
        token = request.COOKIES.get(settings.AUTH_COOKIE_ACCESS_TOKEN_NAME) or None

        if token is None:
            return None

        if len(token) < 10:  # Basic length check
            return None

        jwt_token = JWTToken()
        db_token = jwt_token.decode_token(token)

        if db_token is None:
            return None

        if not db_token.user.is_active:
            return None

        enforce_csrf(request)

        return db_token.user, token

    def authenticate_header(self, request: Request) -> str:
        return "Bearer"
