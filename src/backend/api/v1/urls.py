from django.urls import path, include

urlpatterns = [
    path("ping/", include("api.v1.ping.urls")),
    path("template_options/", include("api.v1.template_options.urls")),
    path("report/", include("api.v1.report.urls")),
    path("costs/", include("api.v1.cost.urls")),
    path("templates/", include("api.v1.template.urls")),
    path("common/", include("api.v1.common.urls")),
    path("aap_auth/", include("api.v1.aap_auth.urls")),
    path("users/", include("api.v1.users.urls")),
]
