import decimal

import pytest

from backend.api.v1.cost.serializers import CostSerializer, CostCreateSerializer
from backend.apps.clusters.models import SubscriptionCost


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_cost_serializer_serializes_subscription_cost():
    obj = SubscriptionCost.get()
    obj.monthly_subscription_cost = decimal.Decimal('1234.56')
    obj.engineer_avg_hourly_rate = decimal.Decimal('78.90')
    obj.save()
    serializer = CostSerializer(obj)
    data = serializer.data
    assert data['monthly_subscription_cost'] == '1234.56'
    assert data['engineer_avg_hourly_rate'] == '78.90'
    assert 'id' in data


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_cost_create_serializer_valid_data_updates_singleton():
    SubscriptionCost.get()
    serializer = CostCreateSerializer(data={
        'monthly_subscription_cost': '999.99',
        'engineer_avg_hourly_rate': '55.55',
    })
    assert serializer.is_valid(), serializer.errors
    updated = serializer.save()
    assert updated.monthly_subscription_cost == decimal.Decimal('999.99')
    assert updated.engineer_avg_hourly_rate == decimal.Decimal('55.55')
    # Ensure singleton is updated
    singleton = SubscriptionCost.get()
    assert singleton.monthly_subscription_cost == decimal.Decimal('999.99')
    assert singleton.engineer_avg_hourly_rate == decimal.Decimal('55.55')


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_cost_create_serializer_missing_fields():
    serializer = CostCreateSerializer(data={})
    assert not serializer.is_valid()
    assert 'monthly_subscription_cost' in serializer.errors
    assert 'engineer_avg_hourly_rate' in serializer.errors


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_cost_create_serializer_invalid_decimal():
    serializer = CostCreateSerializer(data={
        'monthly_subscription_cost': 'not_a_decimal',
        'engineer_avg_hourly_rate': '100.00',
    })
    assert not serializer.is_valid()
    assert 'monthly_subscription_cost' in serializer.errors
    serializer = CostCreateSerializer(data={
        'monthly_subscription_cost': '100.00',
        'engineer_avg_hourly_rate': 'not_a_decimal',
    })
    assert not serializer.is_valid()
    assert 'engineer_avg_hourly_rate' in serializer.errors

@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_cost_create_serializer_out_of_range_values():
    serializer = CostCreateSerializer(data={
        'monthly_subscription_cost': '-1.00',
        'engineer_avg_hourly_rate': '100.00',
    })
    assert not serializer.is_valid()
    assert 'monthly_subscription_cost' in serializer.errors
    serializer = CostCreateSerializer(data={
        'monthly_subscription_cost': '100.00',
        'engineer_avg_hourly_rate': '-1.00',
    })
    assert not serializer.is_valid()
    assert 'engineer_avg_hourly_rate' in serializer.errors
    serializer = CostCreateSerializer(data={
        'monthly_subscription_cost': '1000001.00',
        'engineer_avg_hourly_rate': '100.00',
    })
    assert not serializer.is_valid()
    assert 'monthly_subscription_cost' in serializer.errors
    serializer = CostCreateSerializer(data={
        'monthly_subscription_cost': '100.00',
        'engineer_avg_hourly_rate': '1000.01',
    })
    assert not serializer.is_valid()
    assert 'engineer_avg_hourly_rate' in serializer.errors