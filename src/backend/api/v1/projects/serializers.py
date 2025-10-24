from backend.api.v1.template_options.serializers import FilterKeyValueSerializer
from backend.apps.clusters.models import Project


class ProjectSerializer(FilterKeyValueSerializer[Project]):
    class Meta:
        model = Project
