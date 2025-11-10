from django.db.models import QuerySet
from rest_framework import filters
from rest_framework.request import Request

from backend.apps.clusters.models import DateRangeChoices, Job
from backend.apps.clusters.schemas import DateRangeSchema, QueryParams


def get_filter_options(request: Request) -> QueryParams:
    options = QueryParams()
    fields = type(options).model_fields
    date_range_fields = ["start_date", "end_date", "date_range"]

    for field in fields:
        if field in date_range_fields:
            continue
        values = request.query_params.get(field, None)
        if values:
            values = sorted([int(value) for value in values.split(",")], key=int)
            setattr(options, field, values)

    date_range = request.query_params.get("date_range", None)
    start_date = request.query_params.get("start_date", None)
    end_date = request.query_params.get("end_date", None)

    if date_range is not None:
        options.date_range = DateRangeChoices.get_date_range(
            choice=date_range,
            start=start_date,
            end=end_date,
        )

    return options


class CustomReportFilter(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        options = get_filter_options(request)

        queryset = queryset.organization(options.organization)
        queryset = queryset.cluster(options.cluster)
        queryset = queryset.job_template(options.job_template)
        queryset = queryset.label(options.label)
        queryset = queryset.project(options.project)

        return queryset


def get_range(request: Request) -> DateRangeSchema | None:
    options = get_filter_options(request)
    return options.date_range


def filter_by_range(request: Request, queryset: QuerySet[Job]) -> QuerySet[Job]:
    date_range = get_range(request)

    if date_range:
        start_date = date_range.start
        end_date = date_range.end

        return queryset.after(start_date).before(end_date)

    return queryset
