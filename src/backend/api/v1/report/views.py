import decimal

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import  mixins, filters
from rest_framework.viewsets import GenericViewSet

from backend.api.v1.report.filters import CustomReportFilter
from backend.api.v1.report.serializers import JobSerializer
from backend.apps.clusters.models import Job, JobStatusChoices, CostsChoices
from django.db.models import Count, Sum, F, Q
from backend.apps.clusters.helpers import get_costs

class ReportsView(mixins.ListModelMixin, GenericViewSet):

    filter_backends = [CustomReportFilter, DjangoFilterBackend, filters.OrderingFilter]
    serializer_class = JobSerializer
    ordering_fields = ["name", "successful_runs", "failed_runs",
                       "num_hosts", "elapsed", "manual_time", "manual_costs", "automated_costs", "savings"]
    ordering = ["name"]

    def get_queryset(self):
        costs = get_costs()
        automated_cost_value = costs[CostsChoices.AUTOMATED].value / decimal.Decimal(3600)
        manual_cost_value = costs[CostsChoices.MANUAL].value / decimal.Decimal(60)
        qs = (Job.objects.filter(status__in=[JobStatusChoices.SUCCESSFUL, JobStatusChoices.FAILED]).
                values(
            "name",
            "cluster",
            manual_time=F("job_template__manual_time_minutes"),
        ).annotate(
            runs=Count("id"),
            successful_runs=Count("id", filter=Q(status=JobStatusChoices.SUCCESSFUL)),
            failed_runs=Count("id", filter=Q(status=JobStatusChoices.FAILED)),
            elapsed=Sum("elapsed"),
            num_hosts=Sum("num_hosts"),
            automated_costs=(F("elapsed") * automated_cost_value),
            manual_costs=(F("runs") * F("num_hosts") * F("manual_time") * manual_cost_value),
            savings=(F("manual_costs") - F("automated_costs")),
        ))
        return qs
