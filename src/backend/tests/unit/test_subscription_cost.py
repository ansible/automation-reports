import decimal
from datetime import datetime

import pytest
from django.conf import settings

from backend.apps.clusters.models import SubscriptionCost
from django.db import IntegrityError


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestSubscriptionCost:

    def test_subscription_cost_create(self):
        db = SubscriptionCost.objects.create(
            monthly_subscription_cost=decimal.Decimal(1000),
            engineer_avg_hourly_rate=decimal.Decimal(60),
        )
        db.refresh_from_db()
        assert db.monthly_subscription_cost == decimal.Decimal(1000)
        assert db.engineer_avg_hourly_rate == decimal.Decimal(60)

    def test_subscription_initial_data(self):
        db = SubscriptionCost.get()
        assert db.monthly_subscription_cost == decimal.Decimal(settings.DEFAULT_AUTOMATED_PROCESS_COST)
        assert db.engineer_avg_hourly_rate == decimal.Decimal(settings.DEFAULT_MANUAL_COST_AUTOMATION)

    def test_subscription_cost_update(self):
        db = SubscriptionCost.get()
        db.monthly_subscription_cost = decimal.Decimal(2000)
        db.engineer_avg_hourly_rate = decimal.Decimal(80)
        db.save()
        db.refresh_from_db()
        assert db.monthly_subscription_cost == decimal.Decimal(2000)
        assert db.engineer_avg_hourly_rate == decimal.Decimal(80)

    def test_subscription_cost_unique_record(self):
        SubscriptionCost.get()
        with pytest.raises(IntegrityError):
            SubscriptionCost.objects.create(
                monthly_subscription_cost=decimal.Decimal(1500),
                engineer_avg_hourly_rate=decimal.Decimal(70),
            )

    def test_subscription_cost_string_representation(self):
        db = SubscriptionCost.get()
        expected = f"Monthly Subscription Cost: {db.monthly_subscription_cost}, Engineer Average Hourly Rate: {db.engineer_avg_hourly_rate}"
        assert str(db) == expected

    def test_subscription_cost_min_values(self):
        db = SubscriptionCost.get()
        db.monthly_subscription_cost = decimal.Decimal(0)
        with pytest.raises(ValueError):
            db.save()
        db.engineer_avg_hourly_rate = decimal.Decimal(0)
        with pytest.raises(ValueError):
            db.save()

    def test_subscription_cost_max_values(self):
        db = SubscriptionCost.get()
        db.monthly_subscription_cost = decimal.Decimal('1000000.01')
        with pytest.raises(ValueError):
            db.save()
        db.engineer_avg_hourly_rate = decimal.Decimal(3000)
        with pytest.raises(ValueError):
            db.save()