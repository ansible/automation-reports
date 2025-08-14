import logging

from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request

from backend.apps.aap_auth.jwt_token import JWTToken

logger = logging.getLogger("automation-dashboard")


class AAPAuthentication(BaseAuthentication):
    def authenticate(self, request: Request):
        auth_header = request.headers.get("Authorization", None)

        if not auth_header:
            return None

        token = auth_header.split(" ")[1] if " " in auth_header else None

        if not token:
            return None
        jwt_token = JWTToken()
        db_token = jwt_token.decode_token(token)
        if db_token is None:
            return None

        return db_token.user, None

    def authenticate_header(self, request: Request) -> str:
        return "Bearer"
