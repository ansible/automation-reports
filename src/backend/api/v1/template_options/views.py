import os

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from decimal import Decimal
from backend.api.v1.template_options.serializers import (
    OrganizationSerializer,
    ClusterSerializer,
    LabelSerializer,
    JobTemplateSerializer)
from backend.apps.clusters.helpers import get_costs
from backend.apps.clusters.models import (
    DateRangeChoices,
    Cluster,
    Organization,
    Label,
    JobTemplate, CostsChoices)


class TemplateOptionsView(APIView):

    def get(self, request: Request) -> Response:
        date_range = [
            {
                "key": choice[0], "value": choice[1]
            }
            for choice in DateRangeChoices.choices
        ]
        clusters = Cluster.objects.all().order_by('address')
        organizations = Organization.objects.all().order_by("name")
        labels = Label.objects.all().order_by("name")

        job_templates = JobTemplate.objects.all().order_by("name")

        costs = get_costs()

        result = {
            "clusters": ClusterSerializer(clusters, many=True).data,
            "organizations": OrganizationSerializer(organizations, many=True).data,
            "labels": LabelSerializer(labels, many=True).data,
            "date_ranges": date_range,
            "job_templates": JobTemplateSerializer(job_templates, many=True).data,
            "manual_cost_automation": costs[CostsChoices.MANUAL].value,
            "automated_process_cost": costs[CostsChoices.AUTOMATED].value,
        }

        return Response(
            status=status.HTTP_200_OK,
            data=result)
