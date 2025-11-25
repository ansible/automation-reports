from django.urls import path

from backend.api.v1.metrics.views import MetricsView

urlpatterns = [
    path("", MetricsView.as_view(), name="metrics"),
]
