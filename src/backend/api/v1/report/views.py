import decimal

from django.db.models import Count, Sum, F, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from backend.api.v1.report.filters import CustomReportFilter, filter_by_range, get_range
from backend.api.v1.report.serializers import JobSerializer
from backend.apps.clusters.helpers import get_costs, get_report_data, get_diff_index, get_jobs_chart, get_hosts_chart
from backend.apps.clusters.models import Job, JobStatusChoices, CostsChoices, JobHostSummary


class ReportsView(mixins.ListModelMixin, GenericViewSet):
    filter_backends = [CustomReportFilter, DjangoFilterBackend, filters.OrderingFilter]
    serializer_class = JobSerializer
    ordering_fields = ["name", "successful_runs", "failed_runs",
                       "num_hosts", "elapsed", "manual_time", "manual_costs", "automated_costs", "savings"]
    ordering = ["name"]

    def get_filtered_queryset(self, prev_range=False):
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
        return filter_by_range(self.request, queryset=qs, prev_range=prev_range)

    def get_queryset(self):
        return self.get_filtered_queryset(prev_range=False)

    @action(methods=["get"], detail=False)
    def details(self, request):
        filtered_qs = Job.objects.all()
        filtered_qs = self.filter_queryset(filtered_qs)
        ### TOP USERS ###
        top_users_qs = (filter_by_range(request, filtered_qs).
                        filter(status__in=[JobStatusChoices.SUCCESSFUL, JobStatusChoices.FAILED]))
        top_users_qs = (top_users_qs.filter(launched_by__isnull=False).
                        values(
            user_id=F("launched_by"),
            user_name=F("launched_by__name")
        ).annotate(count=Count("id")).order_by("launched_by").order_by("-count"))[:5]

        qs = self.get_filtered_queryset(prev_range=False)
        prev_qs = self.get_filtered_queryset(prev_range=True)

        report_data = get_report_data(list(qs), list(prev_qs) if prev_qs else [])

        ## UNIQUE HOSTS ###
        host_count_index = None
        host_count_job_qs = filter_by_range(request, filtered_qs)
        host_count = (JobHostSummary.objects.
                      filter(
            job_id__in=host_count_job_qs.values_list("id", flat=True)).values("host").
                      annotate(count=Count("host", distinct=True))).count()

        host_count_job_prev_qs = filter_by_range(request, filtered_qs, prev_range=True)
        if host_count_job_prev_qs:
            prev_host_count = (JobHostSummary.objects.
                               filter(
                job_id__in=host_count_job_prev_qs.values_list("id", flat=True)).values("host").
                               annotate(count=Count("host", distinct=True))).count()

            host_count_index = get_diff_index(prev_host_count, host_count)

        response = {
            "users": list(top_users_qs),
            "total_number_of_unique_hosts": {
                "value": host_count,
                "index": host_count_index
            },

        }
        job_chart_qs = Job.objects.filter(status__in=[JobStatusChoices.SUCCESSFUL, JobStatusChoices.FAILED])
        self.filter_queryset(job_chart_qs)
        job_chart_qs = filter_by_range(request, job_chart_qs)
        job_chart = {"job_chart": get_jobs_chart(job_chart_qs, date_range=get_range(request))}

        hosts_chart = {"host_chart": get_hosts_chart(job_chart_qs, date_range=get_range(request))}

        response_data = {
            **response,
            **report_data,
            **job_chart,
            **hosts_chart,
        }
        return Response(data=response_data, status=status.HTTP_200_OK)
