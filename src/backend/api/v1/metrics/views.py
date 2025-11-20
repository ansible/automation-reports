from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_401_UNAUTHORIZED
from rest_framework.views import APIView

import backend.analytics.subsystem_metrics as s_metrics
from backend.analytics.metrics import metrics
from backend.api import renderers


class MetricsView(APIView):
    renderer_classes = [renderers.PlainTextRenderer, renderers.PrometheusJSONRenderer]

    def initialize_request(self, request, *args, **kwargs):
        if settings.ALLOW_METRICS_FOR_ANONYMOUS_USERS:
            self.permission_classes = (AllowAny,)
        return super(MetricsView, self).initialize_request(request, *args, **kwargs)

    def get(self, request: Request) -> Response:
        if settings.ALLOW_METRICS_FOR_ANONYMOUS_USERS or (
                (request.user and request.user.is_authenticated and (
                        request.user.is_superuser or request.user.is_platform_auditor or request.user.is_staff))):
            metrics_to_show = ''
            if not request.query_params.get('subsystemonly', "0") == "1":
                metrics_to_show += metrics().decode('UTF-8')
            if not request.query_params.get('dbonly', "0") == "1":
                metrics_to_show += s_metrics.metrics(request)
            return Response(metrics_to_show)
        elif request.user.is_authenticated:
            raise PermissionDenied()
        else:
            return Response("Authentication credentials were not provided.", status=HTTP_401_UNAUTHORIZED)
