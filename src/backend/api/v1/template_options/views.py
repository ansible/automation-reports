from rest_framework import status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from backend.apps.instances.models import DateRangeChoices


class TemplateOptionsView(APIView):

    def get(self, request: Request) -> Response:
        organizations = [{"key": i, "value": f"Organization {i}"} for i in range(2, 6)]
        instances = [{"key": i, "value": f"Instance {i}"} for i in range(1,4)]
        templates = [{"key": i, "value": f"Template {i}" if i != 2 else f"Template {i} very looooooooooooooooooooooooooooooooooooooooooong name"} for i in range(1, 40)]

        date_range = [{"key": choice[0], "value": choice[1]} for choice in DateRangeChoices.choices]

        result = {
            "organizations": [{"key": 1, "value": "Default organization"}] + organizations + [{"key": -2, "value": "No organization"}],
            "instances": instances,
            "templates": templates,
            "date_ranges": date_range
        }

        return Response(
            status=status.HTTP_200_OK,
            data=result)
