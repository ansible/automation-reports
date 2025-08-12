from django.urls import path

from backend.api.v1.aap_auth.views import (
    AAPSettingsView,
    AAPTokenView,
    AAPRefreshTokenView,
    AAPLogoutView
)

urlpatterns = [
    path("settings/", AAPSettingsView.as_view(), name="AAPTokenView"),
    path("token/", AAPTokenView.as_view(), name="AAPTokenView"),
    path("refresh_token/", AAPRefreshTokenView.as_view(), name="AAPRefreshTokenView"),
    path("logout/", AAPLogoutView.as_view(), name="LogoutView"),
]
