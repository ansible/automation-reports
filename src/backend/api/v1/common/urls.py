from django.urls import path, include
from rest_framework import routers

from backend.api.v1.common.views.currency import CurrencyView
from backend.api.v1.common.views.filter_set import FilterSetView
from backend.api.v1.common.views.settings import SettingsView

base_router = routers.DefaultRouter()
base_router.register(r"currencies", CurrencyView, basename="currencies")
base_router.register(r"settings", SettingsView, basename="settings")
base_router.register(r"filter_set", FilterSetView, basename="views")
urlpatterns = [
    path("", include(base_router.urls)),
]
