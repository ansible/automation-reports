from django.urls import path, include
from rest_framework import routers

from backend.api.v1.organizations.views import OrganizationView

base_router = routers.DefaultRouter()
base_router.register(r"", OrganizationView, basename="organizations")
urlpatterns = [
    path("", include(base_router.urls)),
]
