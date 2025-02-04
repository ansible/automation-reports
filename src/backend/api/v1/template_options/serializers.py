from rest_framework import serializers

from backend.apps.clusters.models import Organization, Cluster, Label, JobTemplate


class ClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cluster
        fields = ("id", "address")


class OrganizationSerializer(serializers.ModelSerializer):
    key = serializers.IntegerField(read_only=True, source="id")
    value = serializers.CharField(read_only=True, source="name")

    class Meta:
        fields = ("key", "value", "cluster_id")
        model = Organization

class LabelSerializer(serializers.ModelSerializer):
    key = serializers.IntegerField(read_only=True, source="id")
    value = serializers.CharField(read_only=True, source="name")

    class Meta:
        fields = ("key", "value", "cluster_id")
        model = Label

class JobTemplateSerializer(serializers.ModelSerializer):
    key = serializers.IntegerField(read_only=True, source="id")
    value = serializers.CharField(read_only=True, source="name")

    class Meta:
        fields = ("key", "value", "cluster_id")
        model = JobTemplate
