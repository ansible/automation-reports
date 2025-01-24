from rest_framework import serializers

from backend.apps.instances.connector import Connector
from backend.apps.instances.models import Instance


class InstanceSerializer(serializers.ModelSerializer):
  ping = serializers.SerializerMethodField()

  class Meta:
    model = Instance
    fields = ('id', 'host', 'ping')

  @staticmethod
  def get_ping(instance):
    connector = Connector(instance)
    return connector.ping
