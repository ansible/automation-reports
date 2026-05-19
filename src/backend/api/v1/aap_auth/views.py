import logging
from http import HTTPStatus

from django.conf import settings
from django.middleware import csrf
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.api.v1.aap_auth.serializers import AAPAuthSettingsSerializer
from backend.apps.aap_auth.aap_auth import AAPAuth
from backend.apps.aap_auth.models import JwtUserToken, JwtUserRefreshToken

logger = logging.getLogger("automation-dashboard")


def make_response(tokens: dict[str, JwtUserToken | JwtUserRefreshToken]) -> Response:
    response = Response(status=status.HTTP_204_NO_CONTENT)

    response.set_cookie(
        key=settings.AUTH_COOKIE_ACCESS_TOKEN_NAME,
        value=tokens["access_token"].token,
        path=settings.AUTH_COOKIE_PATH,
        expires=tokens["access_token"].expires,
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=settings.AUTH_COOKIE_HTTPONLY,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )

    response.set_cookie(
        key=settings.AUTH_COOKIE_REFRESH_TOKEN_NAME,
        value=tokens["refresh_token"].token,
        path=settings.AUTH_COOKIE_PATH,
        expires=tokens["refresh_token"].expires,
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=settings.AUTH_COOKIE_HTTPONLY,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    return response


class BaseAAPView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def handle_exception(self, exc):
        """
        Django returns 403 Forbidden instead of 401 unauthorized, so an override is required.
        """
        if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
            exc.status_code = status.HTTP_401_UNAUTHORIZED
            exception_handler = self.get_exception_handler()
            context = self.get_exception_handler_context()
            response = exception_handler(exc, context)

            if response is None:
                self.raise_uncaught_exception(exc)

            response.exception = True
            return response

        return super(BaseAAPView, self).handle_exception(exc)


class AAPSettingsView(BaseAAPView):
    serializer_class = AAPAuthSettingsSerializer

    def get(self, request: Request) -> Response:
        try:
            aap_auth = AAPAuth()
        except Exception:
            # AAP auth provider not configured — return empty settings so the
            # frontend can detect this and show a local login fallback.
            return Response(
                data={'name': '', 'url': '', 'client_id': '', 'scope': '', 'approval_prompt': '', 'response_type': ''},
                status=status.HTTP_200_OK,
            )
        return Response(
            data=self.serializer_class(aap_auth.ui_data()).data,
            status=status.HTTP_200_OK
        )


class AAPTokenView(BaseAAPView):

    def post(self, request: Request) -> Response:
        auth_code = request.data.get("auth_code", None)
        redirect_uri = request.data.get("redirect_uri", None)

        if auth_code is None:
            raise AuthenticationFailed("Invalid authorization data for AAP token. 'auth_code' is missing.")

        if redirect_uri is None:
            raise AuthenticationFailed("Invalid redirect URI for AAP token. 'redirect_uri' is missing.")

        aap_auth = AAPAuth()
        try:
            tokens = aap_auth.authorize(auth_code, redirect_uri)
        except Exception as e:
            return Response(data={"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        csrf.get_token(request)
        return make_response(tokens)


class AAPRefreshTokenView(BaseAAPView):
    def post(self, request: Request) -> Response:
        refresh_token = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH_TOKEN_NAME) or None

        if refresh_token is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        aap_auth = AAPAuth()
        try:
            tokens = aap_auth.refresh_token(refresh_token=refresh_token)
        except Exception as e:
            return Response(data={"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        csrf.get_token(request)
        return make_response(tokens)


class DevLoginView(BaseAAPView):
    """Local-account bypass for development (ALLOW_DEV_LOGIN=True only)."""

    def post(self, request: Request) -> Response:
        if not getattr(settings, 'ALLOW_DEV_LOGIN', False):
            return Response(
                {'error': 'Local login is not enabled on this server.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        from django.contrib.auth import authenticate as django_authenticate
        from backend.apps.aap_auth.jwt_token import JWTToken
        from backend.apps.aap_auth.schema import AAPToken

        username = request.data.get('username', '')
        password = request.data.get('password', '')
        django_request = getattr(request, '_request', request)
        user = django_authenticate(django_request, username=username, password=password)
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        dummy_aap_token = AAPToken(
            access_token='dev',
            refresh_token='dev',
            expires_in=86400,
            token_type='Bearer',
        )
        tokens = JWTToken().acquire_token_pair(user=user, aap_token=dummy_aap_token)
        csrf.get_token(request)
        return make_response(tokens)


class AAPLogoutView(BaseAAPView):

    def post(self, request: Request) -> Response:

        access_token = request.COOKIES.get(settings.AUTH_COOKIE_ACCESS_TOKEN_NAME) or None

        if access_token is None:
            refresh_token = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH_TOKEN_NAME)
            if refresh_token is None:
                raise ValueError("Invalid authorization data for AAP logout. 'access_token' is missing.")

            refresh_token_db = JwtUserRefreshToken.get_user_token(refresh_token)
            if refresh_token_db is None:
                raise ValueError("Invalid authorization data for AAP logout. 'access_token' is missing.")
            access_token = refresh_token_db.access_token.token

        aap_auth = AAPAuth()
        result = aap_auth.logout(access_token=access_token)
        if result["success"]:
            return Response(
                data={"message": "You have successfully logged out."},
                status=status.HTTP_200_OK)

        return Response(
            data=result.get("message", "An error occurred while logging out of AAP."),
            status=result.get("status", HTTPStatus.BAD_REQUEST))
