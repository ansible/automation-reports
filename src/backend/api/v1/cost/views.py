from django.db.models import QuerySet
from rest_framework import mixins, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from backend.api.v1.cost.serializers import CostSerializer, CostCreateSerializer
from backend.api.v1.mixins import AdminOnlyViewSet
from backend.apps.clusters.models import Costs, CostsChoices


class CostView(AdminOnlyViewSet, mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    serializer_class = CostSerializer

    def get_queryset(self) -> QuerySet[Costs]:
        return Costs.objects.all()

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = CostCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        value = serializer.data['value']
        _type = serializer.data['type']

        instance = Costs.objects.filter(type=_type).first()
        if instance is None:
            Costs.objects.create(
                value=value,
                type=_type,
            )
        else:
            instance.value = value
            instance.save()

        costs = Costs.get(from_db=True)
        response_data = {
            "manual_cost_automation": costs[CostsChoices.MANUAL],
            "automated_process_cost": costs[CostsChoices.AUTOMATED]
        }
        return Response(data=response_data, status=status.HTTP_202_ACCEPTED)
