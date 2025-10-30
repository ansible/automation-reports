from rest_framework import serializers

from backend.api.v1.template_options.serializers import FilterKeyValueSerializer
from backend.apps.clusters.models import JobTemplate


class TemplatesSerializer(serializers.ModelSerializer[JobTemplate]):
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)

    class Meta:
        model = JobTemplate
        fields = ("id", "name", "description",
                  "time_taken_manually_execute_minutes",
                  "time_taken_create_automation_minutes")


class JobTemplateSerializer(FilterKeyValueSerializer[JobTemplate]):
    class Meta:
        model = JobTemplate
