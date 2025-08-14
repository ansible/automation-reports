from django.urls import path, include
from rest_framework import routers
from backend.api.v1.template_options.views import TemplateOptionsView

base_router = routers.DefaultRouter()
base_router.register(r"", TemplateOptionsView, basename="template_options")

urlpatterns = [
    path("", include(base_router.urls)),
]
