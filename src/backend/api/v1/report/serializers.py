from rest_framework import serializers

from backend.apps.clusters.helpers import sec2time
from backend.apps.clusters.models import Job


class JobSerializer(serializers.ModelSerializer):
    runs = serializers.IntegerField(read_only=True)
    elapsed = serializers.DecimalField(max_digits=10, decimal_places=2)
    elapsed_str = serializers.SerializerMethodField()
    cluster = serializers.IntegerField(read_only=True)
    time_taken_manually_execute_minutes = serializers.IntegerField(read_only=True)
    time_taken_create_automation_minutes = serializers.IntegerField(read_only=True)
    successful_runs = serializers.IntegerField(read_only=True)
    failed_runs = serializers.IntegerField(read_only=True)
    automated_costs = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    manual_costs = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    savings = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    time_savings = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    time_savings_str = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ("name", "runs", "elapsed", "cluster",
                  "elapsed_str", "num_hosts", "time_taken_manually_execute_minutes",
                  "time_taken_create_automation_minutes", "successful_runs",
                  "failed_runs", "automated_costs", "manual_costs", "savings", "job_template_id",
                  "time_savings", "time_savings_str")

    def get_elapsed_str(self, obj):
        return sec2time(obj["elapsed"])

    def get_time_savings_str(self, obj):
        return sec2time(obj["time_savings"])
