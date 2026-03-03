import decimal

from rest_framework import serializers

from backend.apps.clusters.models import SubscriptionCost


class CostSerializer(serializers.ModelSerializer[SubscriptionCost]):
    class Meta:
        model = SubscriptionCost
        fields = ("id", "monthly_subscription_cost", "engineer_avg_hourly_rate")


class CostCreateSerializer(serializers.ModelSerializer[SubscriptionCost]):
    monthly_subscription_cost = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="The monthly subscription cost of the AAP subscription. Must be greater than zero and less than or equal to 1000000.",
    )
    engineer_avg_hourly_rate = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="The average hourly rate for engineers performing manual tasks. Used for cost calculations in reports. Must be greater than zero and less than or equal to 1000.",
    )

    class Meta:
        model = SubscriptionCost
        fields = ("monthly_subscription_cost", "engineer_avg_hourly_rate")

    def validate_engineer_avg_hourly_rate(self, value):
        if value <= decimal.Decimal(0):
            raise serializers.ValidationError("Engineer average hourly rate must be greater than zero.")
        if value > decimal.Decimal(1000):
            raise serializers.ValidationError("Engineer average hourly rate must be less than or equal to 1000.")
        return value

    def validate_monthly_subscription_cost(self, value):
        if value <= decimal.Decimal(0):
            raise serializers.ValidationError("Monthly subscription cost must be greater than zero.")
        if value > decimal.Decimal(1000000):
            raise serializers.ValidationError("Monthly subscription cost must be less than or equal to 1000000.")
        return value

    def create(self, validated_data):
        obj = SubscriptionCost.get()
        obj.monthly_subscription_cost = validated_data["monthly_subscription_cost"]
        obj.engineer_avg_hourly_rate = validated_data["engineer_avg_hourly_rate"]
        obj.save()
        return obj
