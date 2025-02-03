import datetime
import pytz
from django.db import models
from dateutil.relativedelta import relativedelta
import calendar

from backend.apps.clusters.schemas import DateRangeSchema


class Cluster(models.Model):
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

    @classmethod
    def get_date_range(cls, choice, start: str = None, end: str = None)->DateRangeSchema:
        now = datetime.datetime.now(pytz.utc)
        match choice:
            case cls.LAST_YEAR:
                start_date = now.replace(year=now.year - 1, month=1, day=1)
                end_date = now.replace(year=now.year - 1, month=12, day=31)

            case cls.LAST_3_YEARS:
                start_date = now.replace(year=now.year - 3, month=1, day=1)
                end_date = now.replace(year=now.year - 1, month=12, day=31)

            case cls.LAST_2_YEARS:
                start_date = now.replace(year=now.year - 2, month=1, day=1)
                end_date = now.replace(year=now.year - 1, month=12, day=31)

            case cls.LAST_3_MONTH:
                end_date = now - relativedelta(months=1)
                num_days = calendar.monthrange(end_date.year, end_date.month)[1]
                end_date = end_date.replace(day=num_days)
                start_date = now - relativedelta(months=3)
                start_date = start_date.replace(day=1)

            case cls.LAST_6_MONTH:
                end_date = now - relativedelta(months=1)
                num_days = calendar.monthrange(end_date.year, end_date.month)[1]
                end_date = end_date.replace(day=num_days)
                start_date = now - relativedelta(months=6)
                start_date = start_date.replace(day=1)

            case cls.LAST_MONTH:
                end_date = now - relativedelta(months=1)
                num_days = calendar.monthrange(end_date.year, end_date.month)[1]
                end_date = end_date.replace(day=num_days)
                start_date = end_date.replace(day=1)

            case cls.YEAR_TO_DATE:
                end_date = now
                start_date = now.replace(month=1, day=1)

            case cls.MONTH_TO_DATE:
                end_date = now
                start_date = now.replace(day=1)

            case cls.QUARTER_TO_DATE:
                end_date = now
                quarter = (now.month - 1) // 3 + 1
                quarter_start_month = 3 * quarter - 2
                start_date = now.replace(day=1, month=int(quarter_start_month))

            case cls.CUSTOM:
                try:
                    start_date = datetime.datetime.fromisoformat(start)
                except (ValueError, TypeError):
                    start_date = now

                try:
                    end_date = datetime.datetime.fromisoformat(end)
                except (ValueError, TypeError):
                    end_date = now

            case _:
                raise NotImplementedError

        return DateRangeSchema(**{
            'start': datetime.datetime.combine(start_date, datetime.time.min, pytz.utc),
            'end': datetime.datetime.combine(end_date, datetime.time.max, pytz.utc),
        })

