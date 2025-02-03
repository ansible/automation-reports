from rest_framework import filters

from backend.apps.clusters.models import JobLabel, DateRangeChoices


class CustomReportFilter(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        organizations = request.query_params.get("organization", None)
        clusters = request.query_params.get("cluster", None)
        job_templates = request.query_params.get("job_template", None)
        labels = request.query_params.get("label", None)
        date_range_key = request.query_params.get("date_range", None)

        start_date = request.query_params.get("start_date", None)
        end_date = request.query_params.get("end_date", None)

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

        if date_range_key:
            date_range = DateRangeChoices.get_date_range(date_range_key, start_date, end_date).iso_format
            start_date = date_range.get("start", None)
            end_date = date_range.get("end", None)
            if start_date:
                queryset = queryset.filter(finished__gte=start_date)
            if end_date:
                queryset = queryset.filter(finished__lte=end_date)

        return queryset
