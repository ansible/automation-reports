from django.db.models import QuerySet
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from backend.api.v1.template.serializers import TemplateSerializer
from backend.apps.clusters.models import JobTemplate


class TemplateView(mixins.ListModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    serializer_class = TemplateSerializer

    def get_queryset(self) -> QuerySet[JobTemplate]:
        return JobTemplate.objects.all()
