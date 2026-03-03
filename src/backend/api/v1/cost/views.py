from django.db.models import QuerySet
from rest_framework import mixins, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from backend.api.v1.cost.serializers import CostSerializer, CostCreateSerializer
from backend.api.v1.mixins import AdminOnlyViewSet
from backend.apps.clusters.models import SubscriptionCost


class CostView(AdminOnlyViewSet, mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    serializer_class = CostSerializer

    def get_queryset(self) -> QuerySet[SubscriptionCost]:
        return SubscriptionCost.objects.all()

    def list(self, request, *args, **kwargs) -> Response:
        try:
            instance = SubscriptionCost.objects.get(pk=1)
        except SubscriptionCost.DoesNotExist:
            return Response(
                {"detail": "Subscription cost is not initialized."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        serializer = self.get_serializer(instance, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = CostCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_202_ACCEPTED)
