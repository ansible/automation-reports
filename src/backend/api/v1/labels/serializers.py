from backend.api.v1.template_options.serializers import FilterKeyValueSerializer
from backend.apps.clusters.models import Label


class LabelSerializer(FilterKeyValueSerializer[Label]):
    class Meta:
        model = Label
