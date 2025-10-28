import decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Avg
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from backend.api.v1.common.serializers.currency import CurrencySerializer
from backend.api.v1.common.serializers.filter_set import FilterSetSerializer
from backend.api.v1.mixins import AdminOnlyViewSet
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
    Costs, max_minutes_input, min_minutes_input)
from backend.apps.common.models import Currency, Settings, FilterSet


class TemplateOptionsView(AdminOnlyViewSet):

    def list(self, request: Request) -> Response:
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

    @action(methods=["post"], detail=False)
    def restore_user_inputs(self, request: Request) -> Response:
        job_templates = JobTemplate.objects.annotate(
            avg_elapsed=Avg("jobs__elapsed")
        )
        with transaction.atomic():
            for template in list(job_templates):
                if template.avg_elapsed is None:
                    manually_execute_minutes = settings.DEFAULT_TIME_TAKEN_TO_MANUALLY_EXECUTE_MINUTES
                else:
                    manually_execute_minutes = template.avg_elapsed / 60 * 2
                if manually_execute_minutes > max_minutes_input:
                    manually_execute_minutes = max_minutes_input
                elif manually_execute_minutes < min_minutes_input:
                    manually_execute_minutes = min_minutes_input
                template.time_taken_manually_execute_minutes = manually_execute_minutes
                template.time_taken_create_automation_minutes = settings.DEFAULT_TIME_TAKEN_TO_CREATE_AUTOMATION_MINUTES
                template.save()

            costs = Costs.objects.all()
            for cost in costs:
                if cost.type == CostsChoices.MANUAL:
                    cost.value = decimal.Decimal(settings.DEFAULT_MANUAL_COST_AUTOMATION)
                elif cost.type == CostsChoices.AUTOMATED:
                    cost.value = decimal.Decimal(settings.DEFAULT_AUTOMATED_PROCESS_COST)
                else:
                    pass
                cost.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
