from django.urls import path, include
from rest_framework import routers

from backend.api.v1.labels.views import LabelView

base_router = routers.DefaultRouter()
base_router.register(r"", LabelView, basename="labels")
urlpatterns = [
    path("", include(base_router.urls)),
]
