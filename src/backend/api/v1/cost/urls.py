from django.urls import path, include
from rest_framework import routers

from backend.api.v1.cost.views import CostView

base_router = routers.DefaultRouter()
base_router.register(r"", CostView, basename="costs")
urlpatterns = [
    path("", include(base_router.urls)),
]
