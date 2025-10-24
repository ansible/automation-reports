from backend.api.v1.template_options.serializers import FilterKeyValueSerializer
from backend.apps.clusters.models import Organization


class OrganizationSerializer(FilterKeyValueSerializer[Organization]):
    class Meta:
        model = Organization
