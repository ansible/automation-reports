from django.urls import  path
from backend.api.v1.ping.views import PingView

urlpatterns = [
  path("", PingView.as_view(), name="ping"),
]
