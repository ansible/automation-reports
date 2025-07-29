from rest_framework import serializers

from backend.apps.common.models import Settings, SettingsChoices, Currency


class SettingsSerializer(serializers.ModelSerializer[Settings]):
    type = serializers.CharField()

    class Meta:
        model = Settings
        fields = ("type", 'value')

    def create(self, validated_data):
        settings_type = validated_data.pop('type')
        value = validated_data.pop('value')
        instance = Settings.objects.filter(type=settings_type).first()
        if settings_type == SettingsChoices.CURRENCY:
            currency = Currency.objects.filter(pk=value).first()
            if currency is None:
                raise serializers.ValidationError("Currency not found.")
            if instance is not None:
                instance.value = currency.pk
                instance.save()
            else:
                instance = Settings.objects.create(type=SettingsChoices.CURRENCY, value=currency.pk)
            return instance
        elif settings_type == SettingsChoices.ENABLE_TEMPLATE_CREATION_TIME:
            if instance is not None:
                instance.value = value
                instance.save()
            else:
                instance = Settings.objects.create(type=SettingsChoices.ENABLE_TEMPLATE_CREATION_TIME, value=value)
            return instance
        else:
            raise serializers.ValidationError("Not valid type.")
