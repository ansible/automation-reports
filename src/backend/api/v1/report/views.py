import csv
import decimal

from django.db.models import Count, Sum, F, Q
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django_weasyprint.views import WeasyTemplateResponse
from rest_framework import mixins, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from backend.api.v1.report.filters import CustomReportFilter, filter_by_range, get_filter_options
from backend.api.v1.report.serializers import JobSerializer
from backend.apps.clusters.helpers import (
    get_costs,
    get_report_data,
    get_unique_host_count,
    get_chart_data,
    get_related_links,
    sec2time)
from backend.apps.clusters.models import (
    Job,
    JobStatusChoices,
    CostsChoices,
    JobTemplate,
    Organization,
    Label,
    Project)
from backend.apps.common.models import Settings, SettingsChoices, Currency
from backend.django_config import settings


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

    def get_details(self, request):
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
        report_data = get_report_data(qs, prev_qs if prev_qs else None)

        ## TOP PROJECTS ##
        top_projects_qs = (filter_by_range(request, filtered_qs).
                           filter(status__in=[JobStatusChoices.SUCCESSFUL, JobStatusChoices.FAILED], num_hosts__gt=0))
        top_projects_qs = (top_projects_qs.filter(project__isnull=False).values(
            "project_id",
            project_name=F("project__name")
        ).annotate(count=Count("id")).order_by("project_id").order_by("-count"))[:5]

        ## UNIQUE HOSTS ###
        unique_host = get_unique_host_count(options=get_filter_options(request))

        top_data = {
            "users": list(top_users_qs),
            "projects": list(top_projects_qs),
        }

        return {
            **top_data,
            **unique_host,
            **report_data,
        }

    @action(methods=["get"], detail=False)
    def details(self, request):
        details_data = self.get_details(request)
        ## CHARTS ###
        chart_qs = Job.objects.filter(status__in=[JobStatusChoices.SUCCESSFUL, JobStatusChoices.FAILED], num_hosts__gt=0)
        chart_qs = self.filter_queryset(chart_qs)
        chart_qs = filter_by_range(request, chart_qs)
        charts_data = get_chart_data(chart_qs, request=request)

        related_links = get_related_links(request)

        response_data = {
            **details_data,
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

    @action(methods=["post"], detail=False)
    def pdf(self, request):
        table_qs = self.filter_queryset(self.get_base_queryset())

        report_settings = Settings.objects.filter(type=SettingsChoices.CURRENCY).first()
        currency_sign = "$"
        if settings is not None:
            _currency = Currency.objects.filter(pk=report_settings.value).first()
            if _currency is not None:
                currency_sign = _currency.symbol if _currency.symbol else _currency.iso_code

        serializer = JobSerializer(table_qs, many=True)
        details = self.get_details(request)

        options = get_filter_options(request)
        organizations = None
        templates = None
        labels = None
        projects = None
        job_templates = options.get("job_template", None)
        params_organizations = options.get("organization", None)
        params_labels = options.get("label", None)
        params_projects = options.get("project", None)

        if job_templates is not None:
            qs = JobTemplate.objects.filter(id__in=job_templates)
            templates = ", ".join([t.name for t in qs])

        if params_organizations is not None:
            qs = Organization.objects.filter(id__in=params_organizations)
            organizations = ", ".join([o.name for o in qs])

        if params_labels is not None:
            qs = Label.objects.filter(id__in=params_labels)
            labels = ", ".join([l.name for l in qs])

        if params_projects is not None:
            qs = Project.objects.filter(id__in=params_projects)
            projects = ", ".join([p.name for p in qs])

        context = {
            "table_data": serializer.data,
            "details": details,
            "currency": currency_sign,
            "job_chart": request.data.get("job_chart", None),
            "host_chart": request.data.get("host_chart", None),
            "start_date": options["date_range"].start.strftime('%Y-%m-%d'),
            "end_date": options["date_range"].end.strftime('%Y-%m-%d'),
            "templates": templates,
            "organizations": organizations,
            "projects": projects,
            "labels": labels,
        }

        return WeasyTemplateResponse(
            request,
            template='report.html',
            context=context,
            filename='report.pdf',
            headers={
                "Content-Disposition": 'attachment; filename="report.pdf"'
            })
