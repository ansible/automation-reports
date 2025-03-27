from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from backend.api.v1.common.serializers.currency import CurrencySerializer
from backend.apps.common.models import Currency


class CurrencyView(mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    serializer_class = CurrencySerializer

    def get_queryset(self):
        return Currency.objects.all().order_by("name")
