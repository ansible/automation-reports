from dateutil.relativedelta import relativedelta
from rest_framework import serializers

from backend.apps.clusters.models import Job


def sec2time(sec: int) -> str:
    """
    This function converts a number of seconds into a human-readable string format,
    displaying hours, minutes, and seconds.
    It uses `relativedelta` to break down the total seconds and combines days into hours for the output.
    If the total time is less than one hour, it omits the hours part for brevity.
    """
    rd = relativedelta(seconds=sec)
    hours = rd.hours + (24 * rd.days)
    seconds = round(rd.seconds)
    return (
        f"{hours}h {rd.minutes}min {seconds}sec"
        if hours > 0
        else f"{rd.minutes}min {seconds}sec"
    )


class JobSerializer(serializers.ModelSerializer[Job]):
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
