from rest_framework import serializers

from backend.apps.clusters.models import Organization, Cluster, Label, JobTemplate


class ClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cluster
        fields = ("id", "address")


class OrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ("id", "name", "cluster_id")
        model = Organization

class LabelSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ("id", "name", "cluster_id")
        model = Label

class JobTemplateSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ("id", "name", "cluster_id")
        model = JobTemplate
