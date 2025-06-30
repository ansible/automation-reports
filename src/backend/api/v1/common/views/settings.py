from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from backend.api.v1.common.serializers.settings import SettingsSerializer
from backend.apps.common.models import Settings, SettingsChoices


class SettingsView(mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    serializer_class = SettingsSerializer

    def get_queryset(self):
        return Settings.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data
        _type = data.get('type', None)
        if _type is None:
            return Response({"detail": "Type is required."}, status=status.HTTP_400_BAD_REQUEST)

        value = data.get('value', None)
        if _type == SettingsChoices.ENABLE_TEMPLATE_CREATION_TIME:
            value = 1 if value is True else 0
        serializer = self.get_serializer(data={"type": _type, "value": value})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
