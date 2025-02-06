from rest_framework import filters

from backend.apps.clusters.models import JobLabel, DateRangeChoices


def get_filter_options(request):
    options = {}
    params_options = [
        "organization",
        "cluster",
        "job_template",
        "label"
    ]
    for key in params_options:
        values = request.query_params.get(key, None)
        if values is not None:
            options[key] = values.split(",")

    date_range = request.query_params.get("date_range", None)
    start_date = request.query_params.get("start_date", None)
    end_date = request.query_params.get("end_date", None)

    if date_range is not None:
        options["date_range"] = DateRangeChoices.get_date_range(
                choice=date_range,
                start=start_date,
                end=end_date)
    return options


class CustomReportFilter(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        options = get_filter_options(request)

        if options.get("organization", None) is not None:
            queryset = queryset.filter(organization__in=options["organization"])

        if options.get("cluster", None) is not None:
            queryset = queryset.filter(cluster__in=options["cluster"])

        if options.get("job_template", None) is not None:
            queryset = queryset.filter(job_template__in=options["job_template"])

        if options.get("label", None) is not None:
            labels_qs = JobLabel.objects.filter(label_id__in=options["label"]).values_list("job_id", flat=True)
            queryset = queryset.filter(id__in=labels_qs)

        return queryset


def get_range(request):
    options = get_filter_options(request)
    return options.get("date_range", None)


def filter_by_range(request, queryset, prev_range=False):
    date_range = get_range(request)

    if date_range:
        if prev_range:
            start_date = date_range.prev_start
            end_date = date_range.prev_end
            if start_date and end_date:
                queryset = queryset.filter(finished__range=(start_date, end_date))
                return queryset
            return None
        else:
            start_date = date_range.start
            end_date = date_range.end

            if start_date:
                queryset = queryset.filter(finished__gte=start_date)
            if end_date:
                queryset = queryset.filter(finished__lte=end_date)

    return queryset if prev_range is False else None
