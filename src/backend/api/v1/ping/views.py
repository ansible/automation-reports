from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.api.v1.ping.serializers import InstanceSerializer
from backend.apps.instances.models import Instance


class PingView(APIView):

  def get(self, request: Request) -> Response:

    instances = Instance.objects.all()

    return Response(
      status=status.HTTP_200_OK,
      data={
        "ping": "pong",
        "instances": InstanceSerializer(instances, many=True).data
      })
