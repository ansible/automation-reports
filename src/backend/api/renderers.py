from rest_framework import renderers
from prometheus_client.parser import text_string_to_metric_families

class PlainTextRenderer(renderers.BaseRenderer):
    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, media_type=None, renderer_context=None):
        if not isinstance(data, str):
            data = str(data)
        return data.encode(self.charset)


class PrometheusJSONRenderer(renderers.JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, dict):
            # HTTP errors are {'detail': ErrorDetail(string='...', code=...)}
            return super(PrometheusJSONRenderer, self).render(data, accepted_media_type, renderer_context)
        parsed_metrics = text_string_to_metric_families(data)
        data = {}
        for family in parsed_metrics:
            data[family.name] = {}
            data[family.name]['help_text'] = family.documentation
            data[family.name]['type'] = family.type
            data[family.name]['samples'] = []
            for sample in family.samples:
                sample_dict = {"labels": sample[1], "value": sample[2]}
                if family.type == 'histogram':
                    if sample[0].endswith("_sum"):
                        sample_dict['sample_type'] = "sum"
                    elif sample[0].endswith("_count"):
                        sample_dict['sample_type'] = "count"
                    elif sample[0].endswith("_bucket"):
                        sample_dict['sample_type'] = "bucket"
                data[family.name]['samples'].append(sample_dict)
        return super(PrometheusJSONRenderer, self).render(data, accepted_media_type, renderer_context)