from django.db.models import QuerySet
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from backend.api.v1.common.serializers.filter_set import FilterSetSerializer
from backend.api.v1.mixins import AdminOnlyViewSet
from backend.apps.common.models import FilterSet


class FilterSetView(
    AdminOnlyViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin):
    serializer_class = FilterSetSerializer

    def get_queryset(self) -> QuerySet[FilterSet]:
        return FilterSet.objects.all().order_by("name")
