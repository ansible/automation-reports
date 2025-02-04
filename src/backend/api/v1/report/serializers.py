import decimal

from rest_framework import serializers
from backend.apps.clusters.models import Job, Cluster, CostsChoices
from backend.apps.clusters.helpers import get_costs


def sec2time(sec, n_msec=3):
    ''' Convert seconds to 'D days, HH:MM:SS.FFF' '''
    if hasattr(sec,'__len__'):
        return [sec2time(s) for s in sec]
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)

    if d > 0:
        return '%dD %dh %dmin %dsec' % (d, h, m, s)
    elif h > 0:
        return '%dh %dmin %dsec' % (h, m, s)
    else:
        return '%dmin %dsec' % (m, s)

class JobSerializer(serializers.ModelSerializer):
    runs = serializers.IntegerField(read_only=True)
    elapsed = serializers.DecimalField(max_digits=10, decimal_places=3)
    elapsed_str = serializers.SerializerMethodField()
    cluster = serializers.IntegerField(read_only=True)
    manual_time = serializers.IntegerField(read_only=True)
    successful_runs = serializers.IntegerField(read_only=True)
    failed_runs = serializers.IntegerField(read_only=True)
    automated_costs = serializers.DecimalField(max_digits=10, decimal_places=3, read_only=True)
    manual_costs = serializers.DecimalField(max_digits=10, decimal_places=3, read_only=True)
    savings = serializers.DecimalField(max_digits=10, decimal_places=3, read_only=True)

    class Meta:
        model = Job
        fields = ("name", "runs", "elapsed", "cluster",
                  "elapsed_str", "num_hosts", "manual_time",
                  "successful_runs", "failed_runs", "automated_costs",
                  "manual_costs", "savings",)

    def get_elapsed_str(self, obj):
        return sec2time(obj["elapsed"])

