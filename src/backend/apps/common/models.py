from django.db import models

from backend.apps.clusters.models import CreatUpdateModel


class Currency(CreatUpdateModel):
    iso_code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=10)

    class Meta:
        abstract = False

    def __str__(self):
        return self.name


class SettingsChoices(models.TextChoices):
    CURRENCY = "currency", "Currency"
    ENABLE_TEMPLATE_CREATION_TIME = "enable_template_creation_time", "Enable template creation time"


class Settings(CreatUpdateModel):
    type = models.CharField(choices=SettingsChoices.choices, unique=True, max_length=50)
    value = models.BigIntegerField()

    class Meta:
        abstract = False

    def __str__(self):
        return f'{self.type}: {self.value}'

    @classmethod
    def currency(cls):
        qs = cls.objects.filter(type=SettingsChoices.CURRENCY).first()
        if qs is None:
            default_currency = Currency.objects.get(iso_code="USD")
            qs = cls.objects.create(type=SettingsChoices.CURRENCY, value=default_currency.pk)
        return qs.value

    @classmethod
    def enable_template_creation_time(cls):
        qs = cls.objects.filter(type=SettingsChoices.ENABLE_TEMPLATE_CREATION_TIME).first()
        if qs is None:
            default_value = 1
            qs = cls.objects.create(type=SettingsChoices.ENABLE_TEMPLATE_CREATION_TIME, value=default_value)
        return qs.value > 0


class FilterSet(CreatUpdateModel):
    name = models.CharField(max_length=255)
    filters = models.JSONField()

    class Meta:
        abstract = False

    def __str__(self):
        return self.name
