import logging
from http import HTTPStatus

from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.aap_auth.aap_auth import AAPAuth

logger = logging.getLogger("automation-dashboard")


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

    def get(self, request: Request) -> Response:
        aap_auth = AAPAuth()
        data = aap_auth.ui_data()

        return Response(data=data, status=status.HTTP_200_OK)


class AAPTokenView(BaseAAPView):

    def post(self, request: Request) -> Response:
        auth_code = request.data.get("auth_code", None)
        redirect_uri = request.data.get("redirect_uri", None)

        if auth_code is None:
            raise AuthenticationFailed("Invalid authorization data for AAP token. 'auth_code' is missing.")

        if redirect_uri is None:
            raise AuthenticationFailed("Invalid redirect URI for AAP token. 'redirect_uri' is missing.")

        aap_auth = AAPAuth()
        tokens = aap_auth.authorize(auth_code, redirect_uri)

        data = {
            "access_token": tokens["access_token"].token,
            "refresh_token": tokens["refresh_token"].token,
        }

        return Response(data=data, status=status.HTTP_200_OK)


class AAPRefreshTokenView(BaseAAPView):
    def post(self, request: Request) -> Response:
        access_token = request.data.get("access_token", None)
        refresh_token = request.data.get("refresh_token", None)

        if access_token is None:
            raise ValueError("Invalid authorization data for refresh token. 'access_token' is missing.")

        if refresh_token is None:
            raise AuthenticationFailed("Invalid authorization data for refresh token. 'refresh_token' is missing.")

        aap_auth = AAPAuth()
        tokens = aap_auth.refresh_token(access_token=access_token, refresh_token=refresh_token)

        data = {
            "access_token": tokens["access_token"].token,
            "refresh_token": tokens["refresh_token"].token,
        }

        return Response(data=data, status=status.HTTP_200_OK)


class AAPLogoutView(BaseAAPView):
    def post(self, request: Request) -> Response:
        access_token = request.data.get("access_token", None)
        if access_token is None:
            raise ValueError("Invalid authorization data for AAP logout. 'access_token' is missing.")

        aap_auth = AAPAuth()
        result = aap_auth.logout(access_token=access_token)
        if result["success"]:
            return Response(
                data={"You have successfully logged out."},
                status=status.HTTP_200_OK)

        return Response(
            data=result.get("message", "An error occurred while logging out of AAP."),
            status=result.get("status", HTTPStatus.BAD_REQUEST))
