from rest_framework import serializers

from backend.apps.clusters.models import Cluster


class ClusterSerializer(serializers.ModelSerializer[Cluster]):
    class Meta:
        model = Cluster
        fields = ('id', 'address')
