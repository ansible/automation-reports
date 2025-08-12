import pytz
from datetime import datetime, timedelta

from django.db import models

from backend.apps.aap_auth.schema import AAPToken
from backend.apps.users.models import User


class BaseJWTUserToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.TextField(db_index=True)
    jti = models.CharField(unique=True, max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    expires = models.DateTimeField()
    revoked = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @classmethod
    def get_user_token(cls, token: str):
        try:
            return cls.objects.get(token=token, revoked=False)
        except cls.DoesNotExist:
            return None


class JwtUserToken(BaseJWTUserToken):
    aap_token = models.TextField()
    aap_refresh_token = models.TextField()
    aap_token_type = models.CharField(max_length=50)
    aap_token_expires = models.DateTimeField()

    @classmethod
    def create_token(
            cls,
            user: User,
            aap_token: AAPToken,
            token: str,
            jti: str,
            expires: datetime,
    ):
        return JwtUserToken.objects.create(
            user=user,
            token=token,
            jti=jti,
            expires=expires,
            aap_token=aap_token.access_token,
            aap_refresh_token=aap_token.refresh_token,
            aap_token_type=aap_token.token_type,
            aap_token_expires=datetime.now(pytz.utc) + timedelta(seconds=aap_token.expires_in),
        )

    def revoke_token(self):
        self.revoked = True
        self.save(update_fields=['revoked'])
        for refresh_token in self.refresh_tokens.all():
            refresh_token.revoke_token(from_token=True)


class JwtUserRefreshToken(BaseJWTUserToken):
    access_token = models.ForeignKey(JwtUserToken, on_delete=models.CASCADE, related_name='refresh_tokens')

    @classmethod
    def create_token(
            cls,
            user: User,
            access_token: JwtUserToken,
            token: str,
            jti: str,
            expires: datetime):
        return JwtUserRefreshToken.objects.create(
            user=user,
            access_token=access_token,
            token=token,
            jti=jti,
            expires=expires,
        )

    def revoke_token(self, from_token=False):
        self.revoked = True
        self.save(update_fields=['revoked'])
        if not from_token:
            self.access_token.revoked = True
            self.access_token.save(update_fields=['revoked'])
