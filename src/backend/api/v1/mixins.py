from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ViewSet

from backend.api.v1.permissions import IsAdmin
from backend.apps.aap_auth.authentication import AAPAuthentication


class AdminOnlyViewSet(ViewSet):
    authentication_classes = [AAPAuthentication]
    permission_classes = [IsAuthenticated, IsAdmin]
