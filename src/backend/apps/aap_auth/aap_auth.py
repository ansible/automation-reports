import functools
import logging

import requests
import urllib3
from django.conf import settings
from requests import Response
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated

from backend.apps.aap_auth.jwt_token import JWTToken
from backend.apps.aap_auth.models import JwtUserToken, JwtUserRefreshToken
from backend.apps.aap_auth.schema import AAPAuthSettings, AAPToken
from backend.apps.users.models import User
from backend.apps.users.schemas import UserResponseSchema

logger = logging.getLogger("automation-dashboard.aap_auth")


def memoize(func):
    cache = func.cache = {}

    # Inner function to store and retrieve data from the cache
    @functools.wraps(func)
    def inner_cached(*args):
        if 'o_endpoints' in cache:
            return cache['o_endpoints']
        else:
            result = func(*args)
            cache['o_endpoints'] = result
            return result

    return inner_cached

class AAPAuth:
    # Handles AAP authentication and user management

    def __init__(self):
        logger.info("Initializing AAPAuth")
        auth_settings = AAPAuthSettings(**settings.AAP_AUTH_PROVIDER)
        logger.debug(f"Auth settings: {auth_settings}")
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

        logger.info("Fetching OAuth endpoints")
        o_endpoints = self.get_o_endpoints()
        logger.debug(f"OAuth endpoints: {o_endpoints}")

        self.authorize_uri = o_endpoints["authorize_uri"]
        self.token_uri = o_endpoints["token_uri"]
        self.revoke_token_uri = o_endpoints["revoke_token_uri"]

        if not settings.SHOW_URLLIB3_INSECURE_REQUEST_WARNING:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        logger.info("AAPAuth initialized successfully")

    def ping(self, url: str) -> Response:
        logger.info(f"Trying to obtain OAuth endpoint: {url}")
        try:
            response = requests.get(
                url=url,
                verify=self.check_ssl,
                allow_redirects=False,
                timeout=3)
            logger.debug(f"Ping response status: {response.status_code}")
        except requests.exceptions.HTTPError as e:
            logger.error(f'GET request {url} failed: {e}')
            raise AuthenticationFailed(f"Failed request to {url}")
        if response.ok:
            logger.info(f"Successfully obtained OAuth endpoint: {url}")
        return response

    @memoize
    def get_o_endpoints(self):
        logger.info("Getting OAuth endpoints")
        url = f"{self.url}/o/"
        response = self.ping(url)
        logger.debug(f"First endpoint response: {response.ok}")
        if response.ok:
            result = {
                'authorize_uri': '/o/authorize/',
                'token_uri': '/o/token/',
                'revoke_token_uri': '/o/revoke_token/'
            }
            logger.info("OAuth endpoints found at /o/")
            return result

        url = f"{self.url}/api/o/"
        response = self.ping(url)
        logger.debug(f"Second endpoint response: {response.ok}")
        if response.ok:
            result = {
                'authorize_uri': '/api/o/authorize/',
                'token_uri': '/api/o/token/',
                'revoke_token_uri': '/api/o/revoke_token/'
            }
            logger.info("OAuth endpoints found at /api/o/")
            return result
        logger.error("Failed to obtain OAuth endpoints after multiple attempts.")
        raise AuthenticationFailed("Authorization failed: Unable to find a valid OAuth endpoint.")

    def ui_data(self) -> dict[str, str]:
        logger.debug("Preparing UI data for authorization flow")
        return {
            'name': self.name,
            'url': f'{self.url}{self.authorize_uri}',
            'client_id': self.client_id,
            'scope': self.scope,
            'approval_prompt': self.approval_prompt,
            'response_type': 'code',
        }

    def _aap_authorize(self, params: dict[str, str]) -> AAPToken:
        logger.info("Requesting AAP token")
        logger.debug(f"Token request uri: {self.url}{self.token_uri}")
        response = requests.post(
            url=f"{self.url}{self.token_uri}",
            data=params,
            verify=self.check_ssl,
            allow_redirects=False,
            timeout=30,
        )
        logger.debug(f"AAP token response status: {response.status_code}")
        if not response.ok:
            logger.error("Error obtaining AAP token: %s", response.content)
            raise AuthenticationFailed("Obtaining of AAP token failed. An error occurred connecting to AAP authorization server.")

        token_result = response.json()
        logger.debug(f"Token result: {token_result}")
        access_token = token_result.get("access_token", None)
        refresh_token = token_result.get("refresh_token", None)

        if access_token is None or refresh_token is None:
            logger.error("Invalid token response from AAP")
            raise AuthenticationFailed("Obtaining of AAP token failed. Invalid response from AAP.")
        return AAPToken(**token_result)

    def authorize(self, code: str, redirect_uri: str) -> dict[str, JwtUserToken | JwtUserRefreshToken]:
        logger.info("Authorizing user")
        logger.debug(f"Authorization code: {code}, redirect_uri: {redirect_uri}")
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
        logger.info("User authorized successfully")
        return jwt_token.acquire_token_pair(aap_token=aap_token, user=user)

    def get_user_data(self, aap_token: AAPToken) -> User:
        logger.info("Fetching user data from AAP")
        logger.debug(f"Access token: {aap_token.access_token}")
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
            logger.debug(f"User data response status: {user_response.status_code}")
            user_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error("Error obtaining AAP user: %s", e.response.content)
            raise AuthenticationFailed("An error occurred obtaining AAP user.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to validate token with AAP: {str(e)}")
            raise ValueError("Failed to validate token with AAP")

        users = UserResponseSchema(**user_response.json())
        logger.debug(f"User response schema: {users}")
        if users.count != 1:
            logger.error(f"Failed to retrieve AAP user: {str(users)}")
            raise ValueError("Failed to retrieve AAP user.")
        logger.info("User data fetched successfully")
        return User.create_or_update_aap_user(users.results[0])

    def refresh_token(self, refresh_token: str) -> dict[str, JwtUserToken | JwtUserRefreshToken]:
        logger.info("Refreshing JWT token")
        logger.debug(f"Refresh token: {refresh_token}")
        jwt_token = JWTToken()
        refresh_token = jwt_token.decode_refresh_token(token=refresh_token)

        if refresh_token is None:
            logger.error("Refresh token is invalid")
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
        logger.info("JWT token refreshed successfully")
        return jwt_token.acquire_token_pair(aap_token=aap_token, user=user)

    def logout(self, access_token: str) -> dict[str, any]:
        logger.info("Logging out user")
        logger.debug(f"Access token: {access_token}")
        token = JwtUserToken.get_user_token(access_token)
        result = {
            "success": True,
            "message": "",
        }
        if token is None or token.id is None:
            logger.error("Invalid token for logout")
            raise AuthenticationFailed("Invalid token.")

        token_params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "token": token.aap_token,
        }

        response = requests.post(
            url=f'{self.url}{self.revoke_token_uri}',
            data=token_params,
            verify=self.check_ssl,
            allow_redirects=False,
            timeout=30,
        )
        logger.debug(f"Logout response status: {response.status_code}")

        if not response.ok:
            logger.error("Error revoking AAP token: %s", response.content)
            result["success"] = False
            result["message"] = response.content
            result["status_code"] = response.status_code
            return result

        token.revoke_token()
        logger.info("User logged out successfully")
        result["success"] = True
        return result
