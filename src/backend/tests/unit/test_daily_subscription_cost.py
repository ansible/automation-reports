import decimal
from datetime import datetime

import pytest
import pytz
import time_machine
from backend.apps.clusters.models import SubscriptionCost, get_month_overlap_days
from backend.apps.clusters.models import month_range_iter


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestDailySubscriptionCost:

    def test_month_range_iter_same_month(self):
        start = datetime(2023, 5, 1)
        end = datetime(2023, 5, 31)
        result = list(month_range_iter(start, end))
        assert result == [(2023, 5)]

    def test_month_range_iter_multiple_months_same_year(self):
        start = datetime(2023, 3, 1)
        end = datetime(2023, 5, 31)
        result = list(month_range_iter(start, end))
        assert result == [(2023, 3), (2023, 4), (2023, 5)]

    def test_month_range_iter_spanning_years(self):
        start = datetime(2022, 11, 1)
        end = datetime(2023, 2, 28)
        result = list(month_range_iter(start, end))
        assert result == [(2022, 11), (2022, 12), (2023, 1), (2023, 2)]

    def test_month_range_iter_december_to_january(self):
        start = datetime(2023, 12, 1)
        end = datetime(2024, 1, 31)
        result = list(month_range_iter(start, end))
        assert result == [(2023, 12), (2024, 1)]

    def test_month_range_iter_single_day(self):
        start = datetime(2023, 7, 15)
        end = datetime(2023, 7, 15)
        result = list(month_range_iter(start, end))
        assert result == [(2023, 7)]

    def test_full_month_overlap(self):
        # Full month: March 2023
        start = datetime(2023, 3, 1)
        end = datetime(2023, 3, 31)
        month_days, month_start_day, month_end_day = get_month_overlap_days(2023, 3, start, end)
        assert month_days == 31
        assert month_start_day == 1
        assert month_end_day == 31

    def test_partial_first_month(self):
        # Overlap starts on 15th
        start = datetime(2023, 3, 15)
        end = datetime(2023, 3, 31)
        month_days, month_start_day, month_end_day = get_month_overlap_days(2023, 3, start, end)
        assert month_days == 31
        assert month_start_day == 15
        assert month_end_day == 31

    def test_partial_last_month(self):
        # Overlap ends on 10th
        start = datetime(2023, 3, 1)
        end = datetime(2023, 3, 10)
        month_days, month_start_day, month_end_day = get_month_overlap_days(2023, 3, start, end)
        assert month_days == 31
        assert month_start_day == 1
        assert month_end_day == 10

    def test_single_day_overlap(self):
        start = datetime(2023, 3, 20)
        end = datetime(2023, 3, 20)
        month_days, month_start_day, month_end_day = get_month_overlap_days(2023, 3, start, end)
        assert month_days == 31
        assert month_start_day == 20
        assert month_end_day == 20

    def test_february_non_leap_year(self):
        start = datetime(2023, 2, 1)
        end = datetime(2023, 2, 28)
        month_days, month_start_day, month_end_day = get_month_overlap_days(2023, 2, start, end)
        assert month_days == 28
        assert month_start_day == 1
        assert month_end_day == 28

    def test_february_leap_year(self):
        start = datetime(2024, 2, 1)
        end = datetime(2024, 2, 29)
        month_days, month_start_day, month_end_day = get_month_overlap_days(2024, 2, start, end)
        assert month_days == 29
        assert month_start_day == 1
        assert month_end_day == 29

    def test_daily_subscription_cost_partial_first_and_last_month(self):
        db = SubscriptionCost.get()
        db.monthly_subscription_cost = decimal.Decimal('310')  # 10 per day for 31-day month
        db.save()
        # Start: Jan 15, End: Mar 10
        start = datetime(year=2023, month=1, day=15)
        end = datetime(year=2023, month=3, day=10)
        result = db.daily_subscription_cost(start, end)
        # Jan: 15-31 (17 days), Feb: 1-28 (28 days), Mar: 1-10 (10 days)
        jan_days = 31
        feb_days = 28
        mar_days = 31
        jan_overlap = 17
        feb_overlap = 28
        mar_overlap = 10
        total_days = jan_overlap + feb_overlap + mar_overlap
        total_cost = decimal.Decimal('310') * decimal.Decimal(jan_overlap) / decimal.Decimal(jan_days)
        total_cost += decimal.Decimal('310') * decimal.Decimal(feb_overlap) / decimal.Decimal(feb_days)
        total_cost += decimal.Decimal('310') * decimal.Decimal(mar_overlap) / decimal.Decimal(mar_days)
        expected = total_cost / decimal.Decimal(total_days)
        assert result == expected

    def test_daily_subscription_cost_single_day(self):
        db = SubscriptionCost.get()
        db.monthly_subscription_cost = decimal.Decimal('300')
        db.save()
        start = datetime(year=2023, month=2, day=15)
        end = datetime(year=2023, month=2, day=15)
        result = db.daily_subscription_cost(start, end)
        expected = decimal.Decimal('300') / decimal.Decimal(28)  # Feb 2023 has 28 days
        assert result == expected

    def test_daily_subscription_cost_full_month(self):
        db = SubscriptionCost.get()
        db.monthly_subscription_cost = decimal.Decimal('310')
        db.save()
        start = datetime(year=2023, month=1, day=1)
        end = datetime(year=2023, month=1, day=31)
        result = db.daily_subscription_cost(start, end)
        expected = decimal.Decimal('310') / decimal.Decimal(31)
        assert result == expected

    def test_daily_subscription_cost_multiple_months_full(self):
        db = SubscriptionCost.get()
        db.monthly_subscription_cost = decimal.Decimal('300')
        db.save()
        start = datetime(year=2023, month=1, day=1)
        end = datetime(year=2023, month=3, day=31)
        result = db.daily_subscription_cost(start, end)
        jan_days = 31
        feb_days = 28
        mar_days = 31
        total_days = jan_days + feb_days + mar_days
        total_cost = decimal.Decimal('300') * decimal.Decimal(jan_days) / decimal.Decimal(jan_days)
        total_cost += decimal.Decimal('300') * decimal.Decimal(feb_days) / decimal.Decimal(feb_days)
        total_cost += decimal.Decimal('300') * decimal.Decimal(mar_days) / decimal.Decimal(mar_days)
        expected = total_cost / decimal.Decimal(total_days)
        assert result == expected

    @time_machine.travel(datetime(2026, 3, 21, 22, 1, 45, tzinfo=pytz.UTC))
    def test_daily_subscription_cost_no_date(self):
        db = SubscriptionCost.get()
        daily_cost = db.daily_subscription_cost()
        expected_daily_cost = db.monthly_subscription_cost / 31 # March has 31 days
        assert daily_cost == expected_daily_cost

    @time_machine.travel(datetime(2026, 2, 21, 22, 1, 45, tzinfo=pytz.UTC))
    def test_daily_subscription_cost_no_start(self):
        db = SubscriptionCost.get()
        daily_cost = db.daily_subscription_cost(start=None, end=datetime.now())
        expected_daily_cost = db.monthly_subscription_cost / 28 # February 2026 has 28 days
        assert daily_cost == expected_daily_cost

    @time_machine.travel(datetime(2026, 4, 21, 22, 1, 45, tzinfo=pytz.UTC))
    def test_daily_subscription_cost_no_end(self):
        db = SubscriptionCost.get()
        daily_cost = db.daily_subscription_cost(start=datetime.now(), end=None)
        expected_daily_cost = db.monthly_subscription_cost / 30 # April has 30 days
        assert daily_cost == expected_daily_cost

    def test_daily_subscription_cost_start_greater_than_end(self):
        db = SubscriptionCost.get()
        db.monthly_subscription_cost = decimal.Decimal('310')
        db.save()
        start = datetime(year=2023, month=1, day=31)
        end = datetime(year=2023, month=1, day=1)
        result = db.daily_subscription_cost(start, end)
        expected = decimal.Decimal('310') / decimal.Decimal(31)
        assert result == expected
