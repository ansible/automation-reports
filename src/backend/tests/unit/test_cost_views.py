import decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.api.v1.cost.views import CostView
from backend.apps.clusters.models import SubscriptionCost

User = get_user_model()


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_cost_view_list_returns_subscription_cost():
    factory = APIRequestFactory()
    user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
    SubscriptionCost.get()
    view = CostView.as_view({'get': 'list'})
    request = factory.get('/api/v1/cost/')
    force_authenticate(request, user=user)
    response = view(request)
    assert response.status_code == 200
    assert 'monthly_subscription_cost' in response.data
    assert 'engineer_avg_hourly_rate' in response.data


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_cost_view_create_updates_subscription_cost():
    factory = APIRequestFactory()
    user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
    view = CostView.as_view({'post': 'create'})
    data = {
        'monthly_subscription_cost': '888.88',
        'engineer_avg_hourly_rate': '44.44',
    }
    request = factory.post('/api/v1/cost/', data, format='json')
    force_authenticate(request, user=user)
    response = view(request)
    assert response.status_code == 202
    assert response.data['monthly_subscription_cost'] == '888.88'
    assert response.data['engineer_avg_hourly_rate'] == '44.44'
    db = SubscriptionCost.get()
    assert db.monthly_subscription_cost == decimal.Decimal('888.88')
    assert db.engineer_avg_hourly_rate == decimal.Decimal('44.44')


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_cost_view_create_invalid_data():
    factory = APIRequestFactory()
    user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
    view = CostView.as_view({'post': 'create'})
    data = {
        'monthly_subscription_cost': 'not_a_decimal',
        'engineer_avg_hourly_rate': '44.44',
    }
    request = factory.post('/api/v1/cost/', data, format='json')
    force_authenticate(request, user=user)
    response = view(request)
    assert response.status_code == 400
    assert 'monthly_subscription_cost' in response.data


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_cost_view_create_missing_fields():
    factory = APIRequestFactory()
    user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
    view = CostView.as_view({'post': 'create'})
    data = {}
    request = factory.post('/api/v1/cost/', data, format='json')
    force_authenticate(request, user=user)
    response = view(request)
    assert response.status_code == 400
    assert 'monthly_subscription_cost' in response.data
    assert 'engineer_avg_hourly_rate' in response.data
