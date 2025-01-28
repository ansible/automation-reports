from rest_framework import serializers

from backend.apps.clusters.connector import Connector
from backend.apps.clusters.models import Cluster


class ClusterSerializer(serializers.ModelSerializer):
  ping = serializers.SerializerMethodField()

  class Meta:
    model = Cluster
    fields = ('id', 'host', 'ping')

  @staticmethod
  def get_ping(cluster):
    connector = Connector(cluster)
    return connector.ping
