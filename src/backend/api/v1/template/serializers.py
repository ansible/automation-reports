from rest_framework import serializers

from backend.apps.clusters.models import  JobTemplate


class TemplateSerializer(serializers.ModelSerializer):
    name  = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)

    class Meta:
        model = JobTemplate
        fields = ("id", "name", "description", "manual_time_minutes")


