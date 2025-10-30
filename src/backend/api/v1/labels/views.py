from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, filters
from rest_framework.viewsets import GenericViewSet

from backend.api.v1.labels.serializers import LabelSerializer
from backend.api.v1.mixins import AdminOnlyViewSet
from backend.apps.clusters.models import Label


class LabelView(
    AdminOnlyViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    serializer_class = LabelSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    search_fields = ["name"]
    ordering = ["name"]

    def get_queryset(self) -> QuerySet[Label]:
        return Label.objects.all()
