from django.urls import path, include
from rest_framework import routers

from backend.api.v1.report.views import ReportsView

base_router = routers.DefaultRouter()
base_router.register(r"", ReportsView, basename="organization")
urlpatterns = [
    path("", include(base_router.urls)),
]
