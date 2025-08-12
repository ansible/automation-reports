from rest_framework import serializers

from backend.apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'is_superuser', 'is_platform_auditor')
