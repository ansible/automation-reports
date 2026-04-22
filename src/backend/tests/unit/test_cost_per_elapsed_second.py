import decimal
from datetime import datetime

import pytest
import pytz
import time_machine

from backend.apps.clusters.models import SubscriptionCost, get_month_overlap_days
from backend.apps.clusters.models import month_range_iter


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestCostPerElapsedSecond:
    """
    Tests for SubscriptionCost.cost_per_elapsed_second().

    The function returns cost_per_elapsed_second (currency / second) where:
    cost_per_elapsed_second * total_elapsed_seconds_in_period = total_period_cost

    This distributes the proportional monthly subscription cost across all job
    elapsed seconds in the period, so multiplying any job's elapsed (seconds)
    by the returned rate gives that job's share of the subscription cost.
    """

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

    def test_partial_month_overlap(self):
        # Partial month: January 10 - January 20
        start = datetime(2023, 1, 10)
        end = datetime(2023, 1, 20)
        month_days, month_start_day, month_end_day = get_month_overlap_days(2023, 1, start, end)
        assert month_days == 31
        assert month_start_day == 10
        assert month_end_day == 20

    def test_leap_year_february(self):
        # Leap year: February 2024
        start = datetime(2024, 2, 1)
        end = datetime(2024, 2, 29)
        month_days, month_start_day, month_end_day = get_month_overlap_days(2024, 2, start, end)
        assert month_days == 29
        assert month_start_day == 1
        assert month_end_day == 29

    def test_weighted_cost_per_elapsed_unit_full_month(self, jobs):
        """Test weighted cost calculation for a full month with jobs."""
        db = SubscriptionCost.get()
        db.monthly_subscription_cost = decimal.Decimal('2000')
        db.save()

        # Test for March 2025 — only one job falls inside this period (elapsed=25, total=25).
        # The second fixture job is in February and is excluded from this date range.
        start = datetime(2025, 3, 1, tzinfo=pytz.UTC)
        end = datetime(2025, 3, 31, tzinfo=pytz.UTC)

        result = db.cost_per_elapsed_second(start, end)

        # Full month → period_cost == monthly_cost == 2000
        # Total elapsed in period = 25 (one job in March with elapsed=25)
        # Expected cost per elapsed second = 2000 / 25 = 80.0
        expected = decimal.Decimal('2000') / decimal.Decimal('25')
        assert result == expected.quantize(decimal.Decimal('0.0000000001'))

    def test_weighted_cost_per_elapsed_unit_partial_month(self, jobs):
        """Test weighted cost calculation for a partial month."""
        db = SubscriptionCost.get()
        db.monthly_subscription_cost = decimal.Decimal('3100')  # 100 per day for 31-day month
        db.save()

        # Test for March 1-15 (15 days out of 31) - includes the March job finished on 2025-03-01
        start = datetime(2025, 3, 1, tzinfo=pytz.UTC)
        end = datetime(2025, 3, 15, tzinfo=pytz.UTC)

        result = db.cost_per_elapsed_second(start, end)

        # Period cost = 3100 * (15/31) = 1500
        # Total elapsed in period = 25 (one job in March)
        # Expected cost per elapsed unit = 1500 / 25 = 60.0
        period_cost = decimal.Decimal('3100') * decimal.Decimal('15') / decimal.Decimal('31')
        expected = period_cost / decimal.Decimal('25')
        assert result == expected.quantize(decimal.Decimal('0.0000000001'))

    def test_weighted_cost_multiple_months(self, jobs):
        """Test weighted cost calculation across multiple months."""
        db = SubscriptionCost.get()
        db.monthly_subscription_cost = decimal.Decimal('2800')  # 100 per day for 28-day month
        db.save()

        # Test for February-March 2025 (both jobs)
        start = datetime(2025, 2, 1, tzinfo=pytz.UTC)
        end = datetime(2025, 3, 31, tzinfo=pytz.UTC)

        result = db.cost_per_elapsed_second(start, end)

        # February: 2800 * (28/28) = 2800
        # March: 2800 * (31/31) = 2800
        # Total period cost = 2800 + 2800 = 5600
        # Total elapsed = 25 + 25 = 50
        # Expected = 5600 / 50 = 112.0
        expected = decimal.Decimal('5600') / decimal.Decimal('50')
        assert result == expected.quantize(decimal.Decimal('0.0000000001'))

    def test_no_jobs_in_period(self):
        """Test behavior when no jobs exist in the specified period."""
        db = SubscriptionCost.get()
        db.monthly_subscription_cost = decimal.Decimal('2000')
        db.save()

        # Test period with no jobs
        start = datetime(2025, 1, 1, tzinfo=pytz.UTC)
        end = datetime(2025, 1, 31, tzinfo=pytz.UTC)

        result = db.cost_per_elapsed_second(start, end)

        # Should return very small fallback value
        assert result == decimal.Decimal('0.000001')

    @time_machine.travel(datetime(2025, 3, 15, 10, 0, 0, tzinfo=pytz.UTC))
    def test_current_month_default(self, jobs):
        """Test default behavior (no dates specified) uses current month."""
        db = SubscriptionCost.get()
        db.monthly_subscription_cost = decimal.Decimal('3100')
        db.save()

        result = db.cost_per_elapsed_second()

        # Should use March 2025 (current month with one job, elapsed=25)
        # Expected = 3100 / 25 = 124.0
        expected = decimal.Decimal('3100') / decimal.Decimal('25')
        assert result == expected.quantize(decimal.Decimal('0.0000000001'))

    @time_machine.travel(datetime(2025, 1, 15, 10, 0, 0, tzinfo=pytz.UTC))
    def test_current_month_no_jobs(self):
        """Test default behavior when current month has no jobs."""
        db = SubscriptionCost.get()
        db.monthly_subscription_cost = decimal.Decimal('2000')
        db.save()

        result = db.cost_per_elapsed_second()

        # Should return fallback value since no jobs in January
        assert result == decimal.Decimal('0.000001')

    def test_start_greater_than_end(self, jobs):
        """Test that start and end are swapped correctly when start > end."""
        db = SubscriptionCost.get()
        db.monthly_subscription_cost = decimal.Decimal('2000')
        db.save()

        # Reversed dates - should be same as normal order
        start = datetime(2025, 3, 31, tzinfo=pytz.UTC)
        end = datetime(2025, 3, 1, tzinfo=pytz.UTC)

        result = db.cost_per_elapsed_second(start, end)

        # Should be same as March full month test
        expected = decimal.Decimal('2000') / decimal.Decimal('25')
        assert result == expected.quantize(decimal.Decimal('0.0000000001'))

    def test_verification_monthly_cost_distribution(self, jobs):
        """
        Verifies the core invariant:
        cost_per_elapsed_second * total_elapsed_seconds_in_period ≈ total_period_cost

        Uses an explicit tolerance rather than quantize() so that any rounding
        error larger than one unit of the least-significant stored digit
        (per elapsed second) is surfaced as a test failure instead of being
        silently absorbed by rounding.
        """
        db = SubscriptionCost.get()
        db.monthly_subscription_cost = decimal.Decimal('2000')
        db.save()

        # Full month March — one job with elapsed=25 seconds
        start = datetime(2025, 3, 1, tzinfo=pytz.UTC)
        end = datetime(2025, 3, 31, tzinfo=pytz.UTC)

        cost_per_unit = db.cost_per_elapsed_second(start, end)

        total_elapsed_in_period = decimal.Decimal('25')

        # Reconstruct the period cost from the returned per-second rate
        calculated_total_cost = cost_per_unit * total_elapsed_in_period

        expected_period_cost = decimal.Decimal('2000')

        # Tolerance: one unit of the quantization precision (0.0000000001) per
        # elapsed second — any larger discrepancy indicates a real calculation error.
        tolerance = decimal.Decimal('0.0000000001') * total_elapsed_in_period

        assert abs(calculated_total_cost - expected_period_cost) <= tolerance, (
            f"Cost reconstruction error too large: "
            f"|{calculated_total_cost} - {expected_period_cost}| > {tolerance}"
        )
