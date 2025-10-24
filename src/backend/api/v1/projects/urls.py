from django.urls import path, include
from rest_framework import routers

from backend.api.v1.projects.views import ProjectView

base_router = routers.DefaultRouter()
base_router.register(r"", ProjectView, basename="projects")
urlpatterns = [
    path("", include(base_router.urls)),
]
