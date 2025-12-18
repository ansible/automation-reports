import decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Avg
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from backend.api.v1.mixins import AdminOnlyViewSet
from backend.api.v1.template_options.serializers import TemplateOptionsSerializer
from backend.apps.clusters.models import (
    DateRangeChoices,
    Cluster,
    CostsChoices,
    Costs, JobTemplate, max_minutes_input, min_minutes_input)
from backend.apps.common.models import Currency, Settings, FilterSet


class TemplateOptionsView(AdminOnlyViewSet):
    serializer_class = TemplateOptionsSerializer

    def list(self, request: Request) -> Response:
        date_range = [
            {
                "key": choice[0], "value": choice[1]
            }
            for choice in DateRangeChoices.choices
        ]

        costs = Costs.get()

        data = {
            "clusters": Cluster.objects.all().order_by('address'),
            "currencies": Currency.objects.all().order_by("name"),
            "date_ranges": date_range,
            "manual_cost_automation_per_hour": costs[CostsChoices.MANUAL],
            "automated_process_cost_per_minute": costs[CostsChoices.AUTOMATED],
            "currency": Settings.currency(),
            "enable_template_creation_time": Settings.enable_template_creation_time(),
            "filter_sets": FilterSet.objects.all().order_by("name"),
            "max_pdf_job_templates": settings.MAX_PDF_JOB_TEMPLATES,
        }

        return Response(
            status=status.HTTP_200_OK,
            data=self.serializer_class(data).data)

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
                template.time_taken_manually_execute_minutes = int(round(manually_execute_minutes))
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
