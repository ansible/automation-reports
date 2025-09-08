from rest_framework import serializers

from backend.apps.common.models import Currency


class CurrencySerializer(serializers.ModelSerializer[Currency]):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Currency
        fields = ("id", "name", 'iso_code', 'symbol')

    def get_name(self, obj):
        return obj.name.title() if len(obj.name.split()) > 1 else obj.name
