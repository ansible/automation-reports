from rest_framework import serializers

from backend.apps.common.models import Currency


class CurrencySerializer(serializers.ModelSerializer[Currency]):
    class Meta:
        model = Currency
        fields = ("id", "name", 'iso_code', 'symbol')
