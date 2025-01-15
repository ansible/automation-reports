from django.urls import  path, include

urlpatterns = [
  path("ping/", include("api.v1.ping.urls")),
]
