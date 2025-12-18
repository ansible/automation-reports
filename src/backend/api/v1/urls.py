from django.urls import path, include, re_path

from backend.api.schema import schema_view, swagger_ui_view, redoc_view

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
    path("metrics/", include("backend.api.v1.metrics.urls")),
    re_path(r'^schema/$', schema_view, name='schema-json'),
    re_path(r'^docs/$', swagger_ui_view, name='schema-swagger-ui'),
    re_path(r'^redoc/$', redoc_view, name='schema-redoc'),
]
