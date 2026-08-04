import pytest

from backend.apps.clusters.models import SingletonModel, SubscriptionCost
from backend.apps.scheduler.models import SyncScheduleState


@pytest.mark.django_db(reset_sequences=True)
class TestSingletonModel:

    def test_save_forces_pk_to_one(self):
        obj = SubscriptionCost()
        obj.pk = 99
        obj.save()
        assert obj.pk == 1
        assert SubscriptionCost.objects.count() == 1

    def test_get_creates_row_on_first_call(self):
        assert SubscriptionCost.objects.count() == 0
        obj = SubscriptionCost.get()
        assert obj.pk == 1
        assert SubscriptionCost.objects.count() == 1

    def test_get_is_idempotent(self):
        obj1 = SubscriptionCost.get()
        obj2 = SubscriptionCost.get()
        assert obj1.pk == obj2.pk == 1
        assert SubscriptionCost.objects.count() == 1

    def test_second_save_updates_not_inserts(self):
        import decimal
        obj = SubscriptionCost.get()
        obj.engineer_avg_hourly_rate = decimal.Decimal('75.00')
        obj.save()
        assert SubscriptionCost.objects.count() == 1
        refreshed = SubscriptionCost.objects.get(pk=1)
        assert refreshed.engineer_avg_hourly_rate == decimal.Decimal('75.00')

    def test_get_solo_alias_works(self):
        obj = SubscriptionCost.get_solo()
        assert obj.pk == 1

    def test_get_solo_and_get_return_same_object(self):
        obj_get = SubscriptionCost.get()
        obj_solo = SubscriptionCost.get_solo()
        assert obj_get.pk == obj_solo.pk

    def test_sync_schedule_state_get(self):
        state = SyncScheduleState.get()
        assert state.pk == 1

    def test_sync_schedule_state_get_solo(self):
        state = SyncScheduleState.get_solo()
        assert state.pk == 1

    def test_sync_schedule_state_singleton_enforced(self):
        SyncScheduleState.get()
        SyncScheduleState.get()
        assert SyncScheduleState.objects.count() == 1
