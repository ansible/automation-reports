from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from backend.api.v1.common.serializers.settings import SettingsSerializer
from backend.apps.common.models import Settings


class SettingsView(mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    serializer_class = SettingsSerializer

    def get_queryset(self):
        return Settings.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
