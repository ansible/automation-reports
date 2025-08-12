from rest_framework.permissions import BasePermission
from rest_framework.views import APIView
from rest_framework.request import Request


class IsAdmin(BasePermission):

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and (request.user.is_superuser or request.user.is_platform_auditor))
