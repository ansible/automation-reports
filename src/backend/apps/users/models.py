from datetime import datetime

import pytz
from django.contrib.auth.models import AbstractUser
from django.db import models

from backend.apps.users.schemas import UserSchema


class User(AbstractUser):
    is_platform_auditor = models.BooleanField(default=False)

    def log_login(self):
        self.last_login = datetime.now(pytz.utc)
        self.save(update_fields=["last_login"])

    @classmethod
    def create_or_update_aap_user(cls, user_data: UserSchema):
        try:
            user = User.objects.get(username=user_data.username)
        except User.DoesNotExist:
            return User.create_aap_user(user_data)

        user.email = user_data.email
        user.first_name = user_data.first_name
        user.last_name = user_data.last_name
        user.is_platform_auditor = user_data.is_platform_auditor
        user.is_superuser = user_data.is_superuser
        user.save(update_fields=[
            "email",
            "first_name",
            "last_name",
            "is_platform_auditor",
            "is_superuser",
        ])
        return user

    @classmethod
    def create_aap_user(cls, user_data: UserSchema):
        return User.objects.create(
            **user_data.model_dump()
        )
