from rest_framework import serializers


class AAPAuthSettingsSerializer(serializers.Serializer):
    name = serializers.CharField()
    url = serializers.URLField()
    client_id = serializers.CharField()
    scope = serializers.CharField()
    approval_prompt = serializers.CharField()
    response_type = serializers.CharField()
