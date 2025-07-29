from rest_framework import serializers

from backend.apps.common.models import FilterSet


class FilterSetSerializer(serializers.ModelSerializer[FilterSet]):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = FilterSet
        fields = ("id", "name", "filters")

    def validate_name(self, value):
        count_qs = FilterSet.objects.filter(name__iexact=value)
        if self.instance:
            count_qs = count_qs.exclude(pk=self.instance.pk)
        count = count_qs.count()
        if count > 0:
            raise serializers.ValidationError("Filter name already exists.")
        return value
