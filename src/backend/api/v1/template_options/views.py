from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.api.v1.common.serializers.currency import CurrencySerializer
from backend.api.v1.common.serializers.filter_set import FilterSetSerializer
from backend.api.v1.template_options.serializers import (
    OrganizationSerializer,
    ClusterSerializer,
    LabelSerializer,
    JobTemplateSerializer,
    ProjectSerializer)
from backend.apps.clusters.models import (
    DateRangeChoices,
    Cluster,
    Organization,
    Label,
    JobTemplate,
    CostsChoices,
    Project,
    Job,
    Costs)
from backend.apps.common.models import Currency, Settings, FilterSet


class TemplateOptionsView(APIView):

    def get(self, request: Request) -> Response:
        date_range = [
            {
                "key": choice[0], "value": choice[1]
            }
            for choice in DateRangeChoices.choices
        ]
        clusters = Cluster.objects.all().order_by('address')
        organizations = Organization.objects.filter(id__in=Job.objects.values_list('organization', flat=True)).order_by("name")
        labels = Label.objects.all().order_by("name")

        job_templates = JobTemplate.objects.filter(id__in=Job.objects.values_list('job_template', flat=True)).order_by("name")
        currencies = Currency.objects.all().order_by("name")

        costs = Costs.get()

        filter_sets = FilterSet.objects.all().order_by("name")

        projects = Project.objects.all().order_by("name")

        result = {
            "clusters": ClusterSerializer(clusters, many=True).data,
            "currencies": CurrencySerializer(currencies, many=True).data,
            "organizations": OrganizationSerializer(organizations, many=True).data,
            "labels": LabelSerializer(labels, many=True).data,
            "date_ranges": date_range,
            "job_templates": JobTemplateSerializer(job_templates, many=True).data,
            "projects": ProjectSerializer(projects, many=True).data,
            "manual_cost_automation": costs[CostsChoices.MANUAL],
            "automated_process_cost": costs[CostsChoices.AUTOMATED],
            "currency": Settings.currency(),
            "enable_template_creation_time": Settings.enable_template_creation_time(),
            "filter_sets": FilterSetSerializer(filter_sets, many=True).data,
        }

        return Response(
            status=status.HTTP_200_OK,
            data=result)
