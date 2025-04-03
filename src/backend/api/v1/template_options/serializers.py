from rest_framework import serializers

from backend.apps.clusters.models import Organization, Cluster, Label, JobTemplate, Project


class ClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cluster
        fields = ("id", "address")


class FilterKeyValueSerializer(serializers.Serializer):
    key = serializers.IntegerField(read_only=True, source="id")
    value = serializers.CharField(read_only=True, source="name")

    class Meta:
        fields = ("key", "value", "cluster_id")


class OrganizationSerializer(FilterKeyValueSerializer):
    class Meta:
        model = Organization


class LabelSerializer(FilterKeyValueSerializer):
    class Meta:
        model = Label


class JobTemplateSerializer(FilterKeyValueSerializer):
    class Meta:
        model = JobTemplate


class ProjectSerializer(FilterKeyValueSerializer):
    class Meta:
        model = Project
