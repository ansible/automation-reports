import csv
import decimal

from django.db.models import Count, Sum, F, Q
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from backend.api.v1.report.filters import CustomReportFilter, filter_by_range, get_filter_options
from backend.api.v1.report.serializers import JobSerializer
from backend.apps.clusters.helpers import get_costs, get_report_data, get_unique_host_count, get_chart_data, get_related_links, sec2time
from backend.apps.clusters.models import Job, JobStatusChoices, CostsChoices


class ReportsView(mixins.ListModelMixin, GenericViewSet):
    filter_backends = [CustomReportFilter, DjangoFilterBackend, filters.OrderingFilter]
    serializer_class = JobSerializer
    ordering_fields = ["name", "successful_runs", "failed_runs",
                       "num_hosts", "elapsed", "manual_time", "manual_costs",
                       "automated_costs", "savings", "runs"]
    ordering = ["name"]

    def get_base_queryset(self, prev_range=False):
        costs = get_costs()
        automated_cost_value = costs[CostsChoices.AUTOMATED].value / decimal.Decimal(60)
        manual_cost_value = costs[CostsChoices.MANUAL].value
        qs = (
            Job.objects.filter(
                status__in=[JobStatusChoices.SUCCESSFUL, JobStatusChoices.FAILED],
                num_hosts__gt=0
            ).
            values(
                "name",
                "cluster",
                "job_template_id",
                time_taken_manually_execute_minutes=F("job_template__time_taken_manually_execute_minutes"),
                time_taken_create_automation_minutes=F("job_template__time_taken_create_automation_minutes"),
            ).annotate(
                runs=Count("id"),
                successful_runs=Count("id", filter=Q(status=JobStatusChoices.SUCCESSFUL)),
                failed_runs=Count("id", filter=Q(status=JobStatusChoices.FAILED)),
                elapsed=Sum("elapsed"),
                num_hosts=Sum("num_hosts"),
                automated_costs=((F("time_taken_create_automation_minutes") * manual_cost_value) + (F("elapsed") * automated_cost_value)),
                manual_costs=(F("num_hosts") * F("time_taken_manually_execute_minutes") * manual_cost_value),
                manual_time=(F("num_hosts") * (F("time_taken_manually_execute_minutes") * 60)) + (F("time_taken_create_automation_minutes") * 60),
                time_savings=(F("manual_time") - F("elapsed")),
                savings=(F("manual_costs") - F("automated_costs")),
            ))
        return filter_by_range(self.request, queryset=qs, prev_range=prev_range)

    def get_queryset(self):
        return self.get_base_queryset(prev_range=False)

    @action(methods=["get"], detail=False)
    def details(self, request):
        filtered_qs = Job.objects.all()
        filtered_qs = self.filter_queryset(filtered_qs)
        ### TOP USERS ###
        top_users_qs = (filter_by_range(request, filtered_qs)
                        .filter(status__in=[JobStatusChoices.SUCCESSFUL, JobStatusChoices.FAILED], num_hosts__gt=0))
        top_users_qs = (top_users_qs.filter(launched_by__isnull=False, launched_by__type='user').
                        values(
            user_id=F("launched_by"),
            user_name=F("launched_by__name")
        ).annotate(count=Count("id")).order_by("launched_by").order_by("-count"))[:5]

        qs = self.filter_queryset(self.get_base_queryset(prev_range=False))
        prev_qs = self.get_base_queryset(prev_range=True)
        if prev_qs:
            prev_qs = self.filter_queryset(prev_qs)
        report_data = get_report_data(list(qs), list(prev_qs) if prev_qs else [])

        ## TOP PROJECTS ##
        top_projects_qs = (filter_by_range(request, filtered_qs).
                           filter(status__in=[JobStatusChoices.SUCCESSFUL, JobStatusChoices.FAILED], num_hosts__gt=0))
        top_projects_qs = (top_projects_qs.filter(project__isnull=False).values(
            "project_id",
            project_name=F("project__name")
        ).annotate(count=Count("id")).order_by("project_id").order_by("-count"))[:5]

        ## UNIQUE HOSTS ###
        unique_host = get_unique_host_count(options=get_filter_options(request))

        ## CHARTS ###
        chart_qs = Job.objects.filter(status__in=[JobStatusChoices.SUCCESSFUL, JobStatusChoices.FAILED], num_hosts__gt=0)
        chart_qs = self.filter_queryset(chart_qs)
        chart_qs = filter_by_range(request, chart_qs)

        response = {
            "users": list(top_users_qs),
            "projects": list(top_projects_qs),
        }

        charts_data = get_chart_data(chart_qs, request=request)

        related_links = get_related_links(request)

        response_data = {
            **response,
            **unique_host,
            **report_data,
            **charts_data,
            **related_links
        }
        return Response(data=response_data, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False)
    def csv(self, request):
        qs = self.filter_queryset(self.get_base_queryset())
        response = HttpResponse(
            content_type="text/plain",
            headers={"Content-Disposition": 'attachment; filename="report.csv"'},
        )

        writer = csv.writer(response)
        writer.writerow([
            "Name",
            "Number of job executions",
            "Hosts executions",
            "Time taken to manually execute (minutes)",
            "Time taken to create automation (minutes)",
            "Running time (seconds)",
            "Running time",
            "Automated costs",
            "Manual costs",
            "Savings",
        ])
        for job in qs:
            writer.writerow([
                job["name"],
                job["runs"],
                job["num_hosts"],
                job["time_taken_manually_execute_minutes"],
                job["time_taken_create_automation_minutes"],
                job["elapsed"],
                sec2time(job["elapsed"]),
                round(job["automated_costs"], 2),
                round(job["manual_costs"], 2),
                round(job["savings"], 2),
            ])

        return response
