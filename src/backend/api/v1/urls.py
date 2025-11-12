from django.urls import path, include

urlpatterns = [
    path("ping/", include("backend.api.v1.ping.urls")),
    path("template_options/", include("backend.api.v1.template_options.urls")),
    path("report/", include("backend.api.v1.report.urls")),
    path("costs/", include("backend.api.v1.cost.urls")),
    path("templates/", include("backend.api.v1.template.urls")),
    path("common/", include("backend.api.v1.common.urls")),
    path("aap_auth/", include("backend.api.v1.aap_auth.urls")),
    path("users/", include("backend.api.v1.users.urls")),
    path("labels/", include("backend.api.v1.labels.urls")),
    path("projects/", include("backend.api.v1.projects.urls")),
    path("organizations/", include("backend.api.v1.organizations.urls")),
]
