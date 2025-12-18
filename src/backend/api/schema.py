from drf_spectacular.views import SpectacularSwaggerView, SpectacularAPIView, SpectacularRedocView
from rest_framework.permissions import IsAuthenticated


class AuthenticatedSpectacularAPIView(SpectacularAPIView):
    """SpectacularAPIView that requires authentication."""

    permission_classes = [IsAuthenticated]


class AuthenticatedSpectacularSwaggerView(SpectacularSwaggerView):
    """SpectacularSwaggerView that requires authentication."""

    permission_classes = [IsAuthenticated]


class AuthenticatedSpectacularRedocView(SpectacularRedocView):
    """SpectacularRedocView that requires authentication."""

    permission_classes = [IsAuthenticated]


# Schema view (returns OpenAPI schema JSON/YAML)
schema_view = AuthenticatedSpectacularAPIView.as_view()

# Swagger UI view
swagger_ui_view = AuthenticatedSpectacularSwaggerView.as_view(url_name='api:schema-json')

# ReDoc UI view
redoc_view = AuthenticatedSpectacularRedocView.as_view(url_name='api:schema-json')
