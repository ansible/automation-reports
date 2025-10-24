from rest_framework import serializers

from backend.apps.clusters.models import Cluster


class ClusterSerializer(serializers.ModelSerializer[Cluster]):
    class Meta:
        model = Cluster
        fields = ("id", "address")


class FilterKeyValueSerializer(serializers.Serializer):
    key = serializers.IntegerField(read_only=True, source="id")
    value = serializers.CharField(read_only=True, source="name")
    cluster_id = serializers.IntegerField(read_only=True)

    class Meta:
        fields = ("key", "value", "cluster_id")
