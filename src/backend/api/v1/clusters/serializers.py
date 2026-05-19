from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from backend.apps.clusters.models import Cluster, ClusterVersionChoices


class ClusterReadSerializer(serializers.ModelSerializer):
    last_synced = serializers.SerializerMethodField()
    has_access_token = serializers.SerializerMethodField()
    has_refresh_token = serializers.SerializerMethodField()
    has_db_password = serializers.SerializerMethodField()

    class Meta:
        model = Cluster
        fields = [
            'id',
            'protocol',
            'address',
            'port',
            'aap_version',
            'verify_ssl',
            'client_id',
            'last_synced',
            'has_access_token',
            'has_refresh_token',
            'sync_mode',
            'db_host',
            'db_port',
            'db_name',
            'db_user',
            'has_db_password',
        ]

    def get_last_synced(self, obj):
        try:
            return obj.status.last_job_finished_date.isoformat()
        except ObjectDoesNotExist:
            return None

    def get_has_access_token(self, obj):
        return bool(obj.access_token)

    def get_has_refresh_token(self, obj):
        return bool(obj.refresh_token)

    def get_has_db_password(self, obj):
        return bool(obj.db_password)


class ClusterWriteSerializer(serializers.Serializer):
    protocol = serializers.ChoiceField(choices=['http', 'https'])
    address = serializers.CharField(max_length=255)
    port = serializers.IntegerField(default=443, min_value=1, max_value=65535)
    aap_version = serializers.ChoiceField(choices=ClusterVersionChoices.values)
    verify_ssl = serializers.BooleanField(default=True)
    client_id = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    client_secret = serializers.CharField(required=False, allow_blank=True, default='')
    access_token = serializers.CharField(required=False, allow_blank=True, default='')
    refresh_token = serializers.CharField(required=False, allow_blank=True, default='')
    sync_mode = serializers.ChoiceField(choices=['api', 'database'], default='api')
    db_host = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    db_port = serializers.IntegerField(default=5432, required=False)
    db_name = serializers.CharField(max_length=255, required=False, allow_blank=True, default='awx')
    db_user = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    db_password = serializers.CharField(max_length=512, required=False, allow_blank=True, default='')
