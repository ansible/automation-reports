from rest_framework import serializers

from backend.apps.clusters.connector import ApiConnector
from backend.apps.clusters.models import Cluster


class ClusterSerializer(serializers.ModelSerializer):
  ping = serializers.SerializerMethodField()

  class Meta:
    model = Cluster
    fields = ('id', 'host', 'ping')

  @staticmethod
  def get_ping(cluster):
    connector = ApiConnector(cluster)
    return connector.ping
