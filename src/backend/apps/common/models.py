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


class Settings(CreatUpdateModel):
    type = models.CharField(choices=SettingsChoices.choices, unique=True, max_length=20)
    value = models.BigIntegerField()

    class Meta:
        abstract = False

    def __str__(self):
        return f'{self.type}: {self.value}'


class FilterSet(CreatUpdateModel):
    name = models.CharField(max_length=255)
    filters = models.JSONField()

    class Meta:
        abstract = False

    def __str__(self):
        return self.name
