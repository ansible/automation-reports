from rest_framework import serializers

from backend.apps.clusters.models import Costs, CostsChoices


class CostSerializer(serializers.ModelSerializer[Costs]):
    class Meta:
        model = Costs
        fields = ("id", "type", "value")


class CostCreateSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=CostsChoices.choices)
    value = serializers.DecimalField(max_digits=15, decimal_places=2)
