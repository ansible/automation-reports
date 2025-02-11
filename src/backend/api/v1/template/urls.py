from django.urls import path, include
from rest_framework import routers
from backend.api.v1.template.views import TemplateView


base_router = routers.DefaultRouter()
base_router.register(r"", TemplateView, basename="templates")
urlpatterns = [
    path("", include(base_router.urls)),
]
