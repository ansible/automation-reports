from rest_framework import serializers

from backend.apps.clusters.models import ClusterVersionChoices


class ClusterSetupSerializer(serializers.Serializer):
    protocol = serializers.ChoiceField(choices=['http', 'https'])
    address = serializers.CharField(max_length=255)
    port = serializers.IntegerField(default=443, min_value=1, max_value=65535)
    aap_version = serializers.ChoiceField(choices=ClusterVersionChoices.values)
    verify_ssl = serializers.BooleanField(default=True)
    client_id = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    client_secret = serializers.CharField(max_length=1024, required=False, allow_blank=True, default='')
    access_token = serializers.CharField(max_length=1024, required=False, allow_blank=True, default='')
    refresh_token = serializers.CharField(max_length=1024, default='')
    sync_mode = serializers.ChoiceField(choices=['api', 'database'], default='api')
    db_host = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    db_port = serializers.IntegerField(default=5432, required=False)
    db_name = serializers.CharField(max_length=255, required=False, allow_blank=True, default='awx')
    db_user = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    db_password = serializers.CharField(max_length=1024, required=False, allow_blank=True, default='')


class SyncSetupSerializer(serializers.Serializer):
    initial_sync_days = serializers.IntegerField(default=1, min_value=1, required=False)
    initial_sync_since = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        if not attrs.get('initial_sync_since') and not attrs.get('initial_sync_days'):
            attrs['initial_sync_days'] = 1
        return attrs


class CostSetupSerializer(serializers.Serializer):
    monthly_subscription_cost = serializers.DecimalField(max_digits=20, decimal_places=2, min_value=0.01)
    engineer_avg_hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)


class InfraSetupSerializer(serializers.Serializer):
    dashboard_host = serializers.CharField(max_length=255)
    db_host = serializers.CharField(max_length=255)
    db_username = serializers.CharField(max_length=255, default='aapdashboard')
    db_password = serializers.CharField(max_length=255)
    db_name = serializers.CharField(max_length=255, default='aapdashboard')
    db_admin_username = serializers.CharField(max_length=255, default='postgres')
    db_admin_password = serializers.CharField(max_length=255)
    dashboard_admin_password = serializers.CharField(max_length=255)
    nginx_http_port = serializers.IntegerField(default=8083, min_value=1, max_value=65535)
    nginx_https_port = serializers.IntegerField(default=8447, min_value=1, max_value=65535)
    dashboard_tls_cert = serializers.CharField(required=False, allow_blank=True, default='')
    dashboard_tls_key = serializers.CharField(required=False, allow_blank=True, default='')


class SetupConfigureSerializer(serializers.Serializer):
    cluster = ClusterSetupSerializer()
    sync = SyncSetupSerializer()
    costs = CostSetupSerializer()


class SetupInventorySerializer(serializers.Serializer):
    cluster = ClusterSetupSerializer()
    sync = SyncSetupSerializer()
    costs = CostSetupSerializer()
    infra = InfraSetupSerializer()
