from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.api.v1.users.serilaizers import UserSerializer
from backend.apps.aap_auth.authentication import AAPAuthentication


class MeView(APIView):
    authentication_classes = [AAPAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(
            data=UserSerializer(self.request.user).data,
            status=status.HTTP_200_OK
        )
