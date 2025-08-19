import logging

import requests
import urllib3
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated

from backend.apps.aap_auth.jwt_token import JWTToken
from backend.apps.aap_auth.models import JwtUserToken, JwtUserRefreshToken
from backend.apps.aap_auth.schema import AAPAuthSettings, AAPToken
from backend.apps.users.models import User
from backend.apps.users.schemas import UserResponseSchema

logger = logging.getLogger("automation-dashboard")


class AAPAuth:
    # Handles AAP authentication and user management

    def __init__(self):
        # Initialize authentication settings from config
        auth_settings = AAPAuthSettings(**settings.AAP_AUTH_PROVIDER)
        setting_url = auth_settings.url[:-1] if auth_settings.url.endswith('/') else auth_settings.url

        self.name = auth_settings.name
        self.url = f'{auth_settings.protocol}://{setting_url}'
        self.client_id = auth_settings.client_id
        self.client_secret = auth_settings.client_secret
        self.scope = 'read'
        self.approval_prompt = 'auto'

        user_data_uri = auth_settings.user_data_endpoint[1:] if auth_settings.user_data_endpoint.startswith('/') else auth_settings.user_data_endpoint
        self.user_data_uri = user_data_uri
        self.check_ssl = auth_settings.check_ssl

        # Optionally suppress urllib3 SSL warnings
        if not settings.SHOW_URLLIB3_INSECURE_REQUEST_WARNING:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def ui_data(self) -> dict[str, str]:
        # Returns data needed for UI authorization flow
        return {
            'name': self.name,
            'url': f'{self.url}/o/authorize',
            'client_id': self.client_id,
            'scope': self.scope,
            'approval_prompt': self.approval_prompt,
            'response_type': 'code',
        }

    def _aap_authorize(self, params: dict[str, str]) -> AAPToken:
        # Requests an AAP token using provided parameters
        response = requests.post(
            url=f"{self.url}/o/token/",
            data=params,
            verify=self.check_ssl,
            allow_redirects=False,
            timeout=30,
        )
        if not response.ok:
            logger.error("An error occurred obtaining AAP token. %s", response.content)
            raise AuthenticationFailed("Obtaining of AAP token failed. An error occurred connecting to AAP authorization server.")

        token_result = response.json()
        access_token = token_result.get("access_token", None)
        refresh_token = token_result.get("refresh_token", None)

        if access_token is None or refresh_token is None:
            raise AuthenticationFailed("Obtaining of AAP token failed. Invalid response from AAP.")

        return AAPToken(**token_result)

    def authorize(self, code: str, redirect_uri: str) -> dict[str, JwtUserToken | JwtUserRefreshToken]:
        # Exchanges authorization code for tokens and user info
        token_params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "code": code,
        }
        aap_token = self._aap_authorize(token_params)
        user = self.get_user_data(aap_token)
        jwt_token = JWTToken()
        return jwt_token.acquire_token_pair(aap_token=aap_token, user=user)

    def get_user_data(self, aap_token: AAPToken) -> User:
        # Fetches user data from AAP using the access token
        headers = {
            'Authorization': f'{aap_token.token_type} {aap_token.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        try:
            user_response = requests.get(
                url=f'{self.url}/{self.user_data_uri}',
                verify=self.check_ssl,
                allow_redirects=False,
                timeout=30,
                headers=headers
            )
            user_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error("An error occurred obtaining AAP user. %s", e.response.content)
            raise AuthenticationFailed("An error occurred obtaining AAP user.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to validate token with AAP: {str(e)}")
            raise ValueError("Failed to validate token with AAP")

        users = UserResponseSchema(**user_response.json())
        if users.count != 1:
            logger.error(f"Failed to validate token with AAP: {str(users)}")
            raise ValueError("Obtaining of AAP user failed.")
        return User.create_or_update_aap_user(users.results[0])

    def refresh_token(self, refresh_token: str) -> dict[str, JwtUserToken | JwtUserRefreshToken]:
        # Refreshes JWT tokens using the AAP refresh token
        jwt_token = JWTToken()
        refresh_token = jwt_token.decode_refresh_token(token=refresh_token)

        if refresh_token is None:
            raise NotAuthenticated("Refresh token is invalid.")

        token_params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token.access_token.aap_refresh_token,
        }
        aap_token = self._aap_authorize(token_params)
        user = self.get_user_data(aap_token)

        refresh_token.revoke_token()

        return jwt_token.acquire_token_pair(aap_token=aap_token, user=user)

    def logout(self, access_token: str) -> dict[str, any]:
        # Revokes the AAP token and logs out the user
        token = JwtUserToken.get_user_token(access_token)
        result = {
            "success": True,
            "message": "",
        }
        if token is None or token.id is None:
            raise AuthenticationFailed("Invalid token.")

        token_params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "token": token.aap_token,
        }

        response = requests.post(
            url=f'{self.url}/o/revoke_token/',
            data=token_params,
            verify=self.check_ssl,
            allow_redirects=False,
            timeout=30,
        )

        if not response.ok:
            logger.error("An error occurred revoking AAP token. %s", response.content)
            result["success"] = False
            result["message"] = response.content
            result["status_code"] = response.status_code
            return result

        token.revoke_token()
        result["success"] = True
        return result
