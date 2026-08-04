from datetime import timezone

import pytest

from backend.apps.users.models import User
from backend.apps.users.schemas import UserSchema


@pytest.mark.django_db(reset_sequences=True)
class TestUserLogLogin:

    def test_log_login_sets_last_login(self):
        user = User.objects.create_user(username='tester', password='pass')
        assert user.last_login is None
        user.log_login()
        user.refresh_from_db()
        assert user.last_login is not None

    def test_log_login_sets_timezone_aware_datetime(self):
        user = User.objects.create_user(username='tester2', password='pass')
        user.log_login()
        user.refresh_from_db()
        assert user.last_login.tzinfo is not None
        assert user.last_login.utcoffset().total_seconds() == 0

    def test_log_login_updates_on_second_call(self):
        import time
        user = User.objects.create_user(username='tester3', password='pass')
        user.log_login()
        user.refresh_from_db()
        first = user.last_login
        time.sleep(0.01)
        user.log_login()
        user.refresh_from_db()
        assert user.last_login >= first


@pytest.mark.django_db(reset_sequences=True)
class TestCreateAAPUser:

    def test_create_aap_user_basic(self):
        schema = UserSchema(
            username='aapuser',
            email='aap@example.com',
            first_name='AAP',
            last_name='User',
        )
        user = User.create_aap_user(schema)
        assert user.pk is not None
        assert user.username == 'aapuser'
        assert user.email == 'aap@example.com'

    def test_create_aap_user_not_auditor_by_default(self):
        schema = UserSchema(username='plain', email='p@e.com')
        user = User.create_aap_user(schema)
        assert user.is_platform_auditor is False

    def test_create_aap_user_platform_auditor_from_is_platform_auditor(self):
        schema = UserSchema(
            username='auditor',
            email='a@e.com',
            is_platform_auditor=True,
        )
        user = User.create_aap_user(schema)
        assert user.is_platform_auditor is True

    def test_create_aap_user_platform_auditor_from_is_system_auditor(self):
        schema = UserSchema(
            username='sysaudit',
            email='s@e.com',
            is_system_auditor=True,
        )
        user = User.create_aap_user(schema)
        assert user.is_platform_auditor is True


@pytest.mark.django_db(reset_sequences=True)
class TestCreateOrUpdateAAPUser:

    def test_creates_when_user_does_not_exist(self):
        schema = UserSchema(username='newuser', email='new@e.com')
        user = User.create_or_update_aap_user(schema)
        assert User.objects.filter(username='newuser').count() == 1
        assert user.email == 'new@e.com'

    def test_updates_existing_user_fields(self):
        User.objects.create_user(username='existing', email='old@e.com')
        schema = UserSchema(
            username='existing',
            email='new@e.com',
            first_name='Updated',
            last_name='Name',
            is_superuser=True,
        )
        user = User.create_or_update_aap_user(schema)
        assert user.email == 'new@e.com'
        assert user.first_name == 'Updated'
        assert user.is_superuser is True

    def test_does_not_create_duplicate_on_update(self):
        User.objects.create_user(username='dup', email='d@e.com')
        schema = UserSchema(username='dup', email='d2@e.com')
        User.create_or_update_aap_user(schema)
        assert User.objects.filter(username='dup').count() == 1
