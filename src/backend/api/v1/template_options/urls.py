from django.urls import  path
from backend.api.v1.template_options.views import TemplateOptionsView

urlpatterns = [
  path("", TemplateOptionsView.as_view(), name="template_options"),
]
