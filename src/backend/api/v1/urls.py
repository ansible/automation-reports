from django.urls import  path, include

urlpatterns = [
  path("ping/", include("api.v1.ping.urls")),
  path("template_options/", include("api.v1.template_options.urls")),
  path("report/", include("api.v1.report.urls")),
]
