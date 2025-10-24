from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, filters, serializers
from rest_framework.viewsets import GenericViewSet

from backend.api.v1.mixins import AdminOnlyViewSet
from backend.api.v1.template.serializers import TemplateSerializer, JobTemplateSerializer
from backend.apps.clusters.models import JobTemplate


class TemplateView(
    AdminOnlyViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet
):
    serializer_class = TemplateSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    search_fields = ["name"]
    ordering = ["name"]

    def get_serializer_class(self) -> type[serializers.ModelSerializer[JobTemplate]]:
        if self.action == "list" or self.action == "retrieve":
            return JobTemplateSerializer
        return TemplateSerializer

    def get_queryset(self) -> QuerySet[JobTemplate]:
        return JobTemplate.objects.all()
