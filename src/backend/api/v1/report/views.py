import csv
import decimal
import logging
from collections import OrderedDict

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import models
from django.db.models import (
    Count,
    Sum,
    F,
    Q,
    OuterRef,
    Subquery,
    Value,
    QuerySet)
from django.db.models.functions import Trunc, Coalesce
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django_generate_series.models import generate_series
from django_weasyprint.views import WeasyTemplateResponse
from rest_framework import mixins, filters, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from backend.api.v1.report.filters import (
    CustomReportFilter,
    filter_by_range,
    get_filter_options)
from backend.api.v1.report.serializers import (
    JobSerializer,
    sec2time)
from backend.apps.clusters.models import (
    Job,
    JobStatusChoices,
    CostsChoices,
    JobTemplate,
    Organization,
    Label,
    Project,
    JobHostSummary,
    Cluster,
    Costs,
    DateRangeChoices,
    JobLabel)
from backend.apps.clusters.schemas import (
    ReportData,
    ReportDataValue,
    ChartsData,
    ChartItem,
    QueryParams)
from backend.apps.common.models import Settings, Currency
from backend.api.v1.mixins import AdminOnlyViewSet

logger = logging.getLogger("automation-dashboard")


class ReportsView(AdminOnlyViewSet, mixins.ListModelMixin, GenericViewSet):
    filter_backends = [CustomReportFilter, DjangoFilterBackend, filters.OrderingFilter]
    serializer_class = JobSerializer
    ordering_fields = ["name", "successful_runs", "failed_runs",
                       "num_hosts", "elapsed", "manual_time", "manual_costs",
                       "automated_costs", "savings", "runs"]
    ordering = ["name"]

    def get_base_queryset(self) -> QuerySet[Job]:
        costs = Costs.get()
        automated_cost_value = costs[CostsChoices.AUTOMATED] / decimal.Decimal(60)
        manual_cost_value = costs[CostsChoices.MANUAL]

        enable_template_creation_time = Settings.enable_template_creation_time()

        qs = (
            Job.objects.successful_or_failed().
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
                automated_costs=((F("time_taken_create_automation_minutes") * manual_cost_value) + (F("elapsed") * automated_cost_value))
                if enable_template_creation_time
                else (F("elapsed") * automated_cost_value),
                manual_costs=(F("num_hosts") * F("time_taken_manually_execute_minutes") * manual_cost_value),
                manual_time=(F("num_hosts") * (F("time_taken_manually_execute_minutes") * 60)),
                time_savings=(F("manual_time") - F("elapsed") - (F("time_taken_create_automation_minutes") * 60)) if enable_template_creation_time else (F("manual_time") - F("elapsed")),
                savings=(F("manual_costs") - F("automated_costs")),
            ))
        return filter_by_range(self.request, queryset=qs)

    def get_queryset(self) -> QuerySet[Job]:
        return self.get_base_queryset()

    def get_unique_host_count(self, options: QueryParams) -> int:
        qs = (JobHostSummary.objects
        .filter(
            job__num_hosts__gt=0,
            job__status__in=[JobStatusChoices.SUCCESSFUL, JobStatusChoices.FAILED]
        )
        )
        date_range = options.date_range
        if date_range:
            if date_range.start:
                qs = qs.filter(
                    job__finished__gte=date_range.start,
                )
            if date_range.end:
                qs = qs.filter(
                    job__finished__lte=date_range.end,
                )
        for attr in [
            "organization",
            "job_template",
            "project",
            "cluster"]:
            value = getattr(options, attr)
            if value and isinstance(value, list) and len(value) > 0:
                key = f'job__{attr}_id__in'
                qs = qs.filter(
                    **{
                        key: value
                    }
                )
        if options.label and len(options.label) > 0:
            qs = qs.filter(
                job__id__in=JobLabel.objects.filter(label_id__in=options.label).values('job_id')
            )
        qs = qs.values("host_id").distinct()
        return qs.count()

    def get_details(self, request: Request) -> ReportData:
        filtered_qs = Job.objects.successful_or_failed()
        filtered_qs = self.filter_queryset(filtered_qs)
        filtered_qs = filter_by_range(self.request, queryset=filtered_qs)
        ### TOP USERS ###
        top_users_qs = (filtered_qs.filter(launched_by__isnull=False, launched_by__type='user').
                        values(
            user_id=F("launched_by"),
            user_name=F("launched_by__name")
        ).annotate(count=Count("id")).order_by("launched_by").order_by("-count"))[:5]

        ## TOP PROJECTS ##
        top_projects_qs = (filtered_qs.filter(project__isnull=False).values(
            "project_id",
            project_name=F("project__name")
        ).annotate(count=Count("id")).order_by("project_id").order_by("-count"))[:5]

        ## UNIQUE HOSTS ###
        unique_host = self.get_unique_host_count(options=get_filter_options(request))

        qs = self.filter_queryset(self.get_base_queryset())

        report_data_qs = qs.aggregate(
            total_runs=Sum("runs"),
            total_successful_runs=Sum("successful_runs"),
            total_failed_runs=Sum("failed_runs"),
            total_num_hosts=Sum("num_hosts"),
            total_elapsed=Sum("elapsed"),
            total_manual_time=Sum("manual_time"),
            total_manual_costs=Sum("manual_costs"),
            total_automated_costs=Sum("automated_costs"),
            total_savings=Sum("savings"),
            total_time_savings=Sum("time_savings"),
        )

        report_data = ReportData(
            total_number_of_unique_hosts=ReportDataValue(value=unique_host),
            total_number_of_successful_jobs=ReportDataValue(value=report_data_qs["total_successful_runs"]),
            total_number_of_failed_jobs=ReportDataValue(value=report_data_qs["total_failed_runs"]),
            total_number_of_job_runs=ReportDataValue(value=report_data_qs["total_runs"]),
            total_number_of_host_job_runs=ReportDataValue(value=report_data_qs["total_num_hosts"]),
            total_hours_of_automation=ReportDataValue(
                value=round((report_data_qs["total_elapsed"] / 3600), 2) if report_data_qs["total_elapsed"] is not None else 0),
            cost_of_automated_execution=ReportDataValue(
                value=round(report_data_qs["total_automated_costs"], 2) if report_data_qs["total_automated_costs"] is not None else 0
            ),
            cost_of_manual_automation=ReportDataValue(
                value=round(report_data_qs["total_manual_costs"], 2) if report_data_qs["total_manual_costs"] is not None else 0
            ),
            total_saving=ReportDataValue(
                value=round(report_data_qs["total_savings"], 2) if report_data_qs["total_savings"] is not None else 0
            ),
            total_time_saving=ReportDataValue(
                value=round((report_data_qs["total_time_savings"] / 3600), 2) if report_data_qs["total_time_savings"] is not None else 0
            ),
            users=list(top_users_qs),
            projects=list(top_projects_qs),
        )

        return report_data

    def get_chart_series(self, options: QueryParams) -> ChartsData:
        result = ChartsData()

        date_range = options.date_range
        if date_range is None:
            logger.debug(f"Date range is empty. {options}")
            return result

        start_date = date_range.start
        end_date = date_range.end

        kind = DateRangeChoices.db_kind(start_date, end_date)
        result.host_chart.range = kind
        result.job_chart.range = kind

        if start_date is None or end_date is None:
            logger.debug(f"Start date or end date is empty. {options}")
            return result

        if kind == 'month' or kind == 'year':
            start_date = start_date.replace(day=1)
            end_date = end_date.replace(day=1)

        base_chart_qs = (Job.objects
        .successful_or_failed()
        .values(
            date=Trunc(
                expression="finished",
                kind=kind,
                output_field=models.DateTimeField()))
        .filter(
            date=OuterRef("term")
        ))

        base_chart_qs = self.filter_queryset(base_chart_qs)
        base_chart_qs = filter_by_range(self.request, queryset=base_chart_qs)

        job_chart_qs = base_chart_qs.annotate(
            runs=Count("id")
        ).values("runs").order_by()

        host_chart_qs = base_chart_qs.annotate(
            num_hosts=Sum("num_hosts")
        ).values("num_hosts").order_by()

        date_sequence_queryset = generate_series(
            start=start_date,
            stop=end_date,
            step=f'1 {kind}s',
            span=5,
            output_field=models.DateTimeField
        ).annotate(
            runs=Coalesce(Subquery(job_chart_qs), Value(0)),
            hosts=Coalesce(Subquery(host_chart_qs), Value(0)),
        )

        for data in date_sequence_queryset:
            result.job_chart.items.append(
                ChartItem(x=data.term, y=data.runs),
            )
            result.host_chart.items.append(
                ChartItem(x=data.term, y=data.hosts),
            )

        return result

    @action(methods=["get"], detail=False)
    def details(self, request: Request) -> Response:
        options = get_filter_options(request)

        details_data = self.get_details(request)

        ## CHARTS ###
        charts_data = self.get_chart_series(options)

        related_links = Cluster.related_links(options.date_range)

        response_data = {
            **details_data.model_dump(),
            **charts_data.model_dump(),
            **related_links,
        }

        return Response(data=response_data, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False)
    def csv(self, request: Request) -> Response:
        qs = self.filter_queryset(self.get_base_queryset())
        response = HttpResponse(
            content_type="text/csv; charset=UTF-8",
            headers={"Content-Disposition": 'attachment; filename="AAP_Automation_Dashboard_Report.csv"'},
        )

        enable_template_creation_time = Settings.enable_template_creation_time()

        writer = csv.writer(response)
        rows = [
            "Name",
            "Number of job executions",
            "Hosts executions",
            "Time taken to manually execute (minutes)",
        ]

        if enable_template_creation_time:
            rows.append("Time taken to create automation (minutes)")

        rows += [
            "Running time (seconds)",
            "Running time",
            "Automated costs",
            "Manual costs",
            "Savings",
        ]

        writer.writerow(rows)
        for job in qs:
            row = [
                job["name"],
                job["runs"],
                job["num_hosts"],
                job["time_taken_manually_execute_minutes"],

            ]
            if enable_template_creation_time:
                row.append(job["time_taken_create_automation_minutes"])
            row += [
                job["elapsed"],
                sec2time(job["elapsed"]),
                round(job["automated_costs"], 2),
                round(job["manual_costs"], 2),
                round(job["savings"], 2),
            ]
            writer.writerow(row)

        return response

    @action(methods=["post"], detail=False)
    def pdf(self, request: Request) -> WeasyTemplateResponse:
        table_qs = self.filter_queryset(self.get_base_queryset())[:settings.MAX_PDF_JOB_TEMPLATES]

        currency_value = Settings.currency()
        currency_sign = "$"
        if settings is not None:
            _currency = Currency.objects.filter(pk=currency_value).first()
            if _currency is not None:
                currency_sign = _currency.symbol if _currency.symbol else _currency.iso_code

        serializer = JobSerializer(table_qs, many=True)
        details = self.get_details(request)

        options = get_filter_options(request)

        options_data = OrderedDict()

        for param in [
            ("job_template", JobTemplate, "Template"),
            ("organization", Organization, "Organization"),
            ("project", Project, "Project"),
            ("label", Label, "Label"),
        ]:
            param_data = getattr(options, param[0], None)
            if param_data is not None:
                qs = param[1].objects.filter(id__in=param_data)
                options_data[param[0]] = {
                    "name": param[2],
                    "values": ", ".join([t.name for t in qs])
                }

        context = {
            "table_data": serializer.data,
            "details": details,
            "currency": currency_sign,
            "job_chart": request.data.get("job_chart", None),
            "host_chart": request.data.get("host_chart", None),
            "start_date": options.date_range.start.strftime('%Y-%m-%d'),
            "end_date": options.date_range.end.strftime('%Y-%m-%d'),
            "filters": options_data,
            "enable_template_creation_time": Settings.enable_template_creation_time()
        }

        return WeasyTemplateResponse(
            request,
            template='report.html',
            context=context,
            filename='AAP_Automation_Dashboard_Report.PDF',
            headers={
                "Content-Disposition": 'attachment; filename="AAP_Automation_Dashboard_Report.pdf"'
            })
