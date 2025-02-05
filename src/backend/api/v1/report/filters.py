from rest_framework import filters

from backend.apps.clusters.models import JobLabel, DateRangeChoices


class CustomReportFilter(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        organizations = request.query_params.get("organization", None)
        clusters = request.query_params.get("cluster", None)
        job_templates = request.query_params.get("job_template", None)
        labels = request.query_params.get("label", None)

        if organizations:
            list_organizations = [int(org) for org in organizations.split(",")]
            queryset = queryset.filter(organization__in=list_organizations)

        if clusters:
            list_clusters = [int(cluster) for cluster in clusters.split(",")]
            queryset = queryset.filter(cluster__in=list_clusters)

        if job_templates:
            list_job_templates = [int(template) for template in job_templates.split(",")]
            queryset = queryset.filter(job_template__in=list_job_templates)

        if labels:
            list_labels = [int(label) for label in labels.split(",")]
            labels_qs = JobLabel.objects.filter(label_id__in=list_labels).values_list("job_id", flat=True)
            queryset = queryset.filter(id__in=labels_qs)

        return queryset


def get_range(request):
    date_range_key = request.query_params.get("date_range", None)
    start_date = request.query_params.get("start_date", None)
    end_date = request.query_params.get("end_date", None)

    if date_range_key:
        return DateRangeChoices.get_date_range(date_range_key, start_date, end_date)
    return None


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
