from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins

from backend.api.v1.common.serializers.filter_set import FilterSetSerializer
from backend.apps.common.models import FilterSet


class FilterSetView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin):

    serializer_class = FilterSetSerializer

    def get_queryset(self):
        return FilterSet.objects.all().order_by("name")
