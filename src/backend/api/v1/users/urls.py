from django.urls import path

from backend.api.v1.users.views import MeView

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
]
