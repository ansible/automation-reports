from django.urls import path

from backend.api.v1.template_options.views import TemplateOptionsView

urlpatterns = [
    path("", TemplateOptionsView.as_view({'get': 'get'}), name="template_options"),
]
