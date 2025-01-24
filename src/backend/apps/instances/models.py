from django.db import models


class Instance(models.Model):
    protocol = models.CharField(max_length=10)
    host = models.CharField(max_length=15)
    port = models.IntegerField()
    access_token = models.TextField()
    verify_ssl = models.BooleanField(default=True)

    objects = models.Manager()

    def __str__(self):
        return f'{self.protocol}://{self.host}:{self.port}'


class DateRangeChoices(models.TextChoices):
    LAST_YEAR = "last_year", "Past year"
    LAST_6_MONTH = "last_6_month", "Past 6 months"
    LAST_3_MONTH = "last_3_month", "Past 3 months"
    LAST_MONTH = "last_month", "Past month"
    YEAR_TO_DATE = "year_to_date", "Year to date"
    QUARTER_TO_DATE = "quarter_to_date", "Quarter to date"
    MONTH_TO_DATE = "month_to_date", "Month to date"
    LAST_3_YEARS = "last_3_years", "Past 3 years"
    LAST_2_YEARS = "last_2_years", "Past 2 years"
    CUSTOM = "custom", "Custom"
