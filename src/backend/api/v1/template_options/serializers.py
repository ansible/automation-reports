from rest_framework import serializers

from backend.api.v1.common.serializers.currency import CurrencySerializer
from backend.api.v1.common.serializers.filter_set import FilterSetSerializer
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


class DateRangeSerializer(serializers.Serializer):
    key = serializers.CharField()
    value = serializers.CharField()


class TemplateOptionsSerializer(serializers.Serializer):
    clusters = ClusterSerializer(many=True)
    currencies = CurrencySerializer(many=True)
    date_ranges = DateRangeSerializer(many=True)
    manual_cost_automation_per_hour = serializers.DecimalField(max_digits=15, decimal_places=2)
    automated_process_cost_per_minute = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency = serializers.IntegerField()
    enable_template_creation_time = serializers.BooleanField()
    filter_sets = FilterSetSerializer(many=True)
    max_pdf_job_templates = serializers.IntegerField()
