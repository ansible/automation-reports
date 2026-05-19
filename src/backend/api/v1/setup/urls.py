from django.urls import path

from .views import (
    SetupStatusView,
    SetupMeView,
    SetupLocalLoginView,
    SetupTestConnectionView,
    SetupConfigureView,
    SetupInventoryView,
    SetupSyncProgressView,
)

urlpatterns = [
    path('status/', SetupStatusView.as_view(), name='setup-status'),
    path('me/', SetupMeView.as_view(), name='setup-me'),
    path('local_login/', SetupLocalLoginView.as_view(), name='setup-local-login'),
    path('test_connection/', SetupTestConnectionView.as_view(), name='setup-test-connection'),
    path('configure/', SetupConfigureView.as_view(), name='setup-configure'),
    path('inventory/', SetupInventoryView.as_view(), name='setup-inventory'),
    path('sync_progress/', SetupSyncProgressView.as_view(), name='setup-sync-progress'),
]
