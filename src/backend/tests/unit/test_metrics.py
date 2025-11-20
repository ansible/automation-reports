import unittest
from unittest.mock import MagicMock, patch

import pytest
from prometheus_client.parser import text_string_to_metric_families

from backend.analytics.collectors import job_counts
from backend.analytics.metrics import metrics
from backend.analytics.subsystem_metrics import BaseM, FloatM, IntM, SetIntM, SetFloatM, \
    HistogramM, MetricsNamespace, Metrics, CustomToPrometheusMetricsCollector, MetricsServerSettings, \
    MetricsServer

test_job_counts_empty_expected_data = {
    'total_jobs': 0,
    'status': {},
    'launch_type': {},
    'type': {}
}

test_job_counts_with_jobs_expected_data = {
    'total_jobs': 6,
    'status': {
        'pending': 2,
        'failed': 1,
        'successful': 1,
        'running': 2
    },
    'launch_type': {
        'auto': 6
    },
    'type': {
        'Parse job data': 3,
        'Sync jobs': 3
    }
}

test_metrics_expected_data = {
    'automation_dashboard_jobs_total': 6.0,
    'automation_dashboard_status_total':
        {
            'canceled': 0.0,
            'running': 2.0,
            'waiting': 0.0,
            'successful': 1.0,
            'error': 0.0,
            'failed': 1.0,
            'pending': 2.0
        },
    'automation_dashboard_type_total': {
        'Parse job data': 3.0,
        'Sync jobs': 3.0
    }
}


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestMetrics:

    @pytest.mark.parametrize('expected', [test_job_counts_empty_expected_data])
    def test_job_counts_empty(self, expected):
        counts = job_counts()
        assert counts == expected

    @pytest.mark.parametrize('expected', [test_job_counts_with_jobs_expected_data])
    def test_job_counts_with_jobs(self, sync_jobs, expected):
        counts = job_counts()
        assert counts == expected

    @pytest.mark.parametrize('expected', [test_metrics_expected_data])
    def test_metrics(self, sync_jobs, expected):
        output = metrics().decode('utf-8')
        gauges = text_string_to_metric_families(output)
        values = {}
        for gauge in gauges:
            for sample in gauge.samples:
                # name, label, value, timestamp, exemplar
                name, label, value, _, _, _ = sample
                _v = values.get(name, {})
                if label:
                    _v_label = label.popitem()
                    _v[_v_label[1]] = value
                else:
                    _v = value
                values[name] = _v

        assert values == expected


class TestBaseM(unittest.TestCase):
    def test_init_and_methods(self):
        m = BaseM('field', 'help')
        self.assertEqual(m.field, 'field')
        self.assertEqual(m.help_text, 'help')
        m.inc(5)
        self.assertEqual(m.get(), 5)
        m.set(10)
        self.assertEqual(m.get(), 10)


class TestFloatM(unittest.TestCase):
    def test_decode_and_store(self):
        m = FloatM('field', 'help')
        self.assertEqual(m.decode_value('2.5'), 2.5)
        conn = MagicMock()
        m.inc(1.5)
        m.store_value(conn)
        conn.hincrbyfloat.assert_called()


class TestIntM(unittest.TestCase):
    def test_decode_and_store(self):
        m = IntM('field', 'help')
        self.assertEqual(m.decode_value('2'), 2)
        conn = MagicMock()
        m.inc(2)
        m.store_value(conn)
        conn.hincrby.assert_called()


class TestSetIntM(unittest.TestCase):
    def test_decode_and_store(self):
        m = SetIntM('field', 'help')
        self.assertEqual(m.decode_value('3'), 3)
        conn = MagicMock()
        m.set(5)
        m.store_value(conn)
        conn.hset.assert_called()


class TestSetFloatM(unittest.TestCase):
    def test_decode_and_store(self):
        m = SetFloatM('field', 'help')
        self.assertEqual(m.decode_value('3.5'), 3.5)
        conn = MagicMock()
        m.set(7.5)
        m.store_value(conn)
        conn.hset.assert_called()


class TestHistogramM(unittest.TestCase):
    def test_observe_and_decode(self):
        m = HistogramM('hist', 'help', [1, 2, 3])
        m.observe(2)
        conn = MagicMock()
        m.decode(conn)
        m.store_value(conn)
        self.assertTrue(hasattr(m, 'buckets'))


class TestMetricsNamespace(unittest.TestCase):
    def test_init(self):
        ns = MetricsNamespace('ns')
        self.assertEqual(ns.namespace, 'ns')


class TestSMetrics(unittest.TestCase):
    @patch('backend.analytics.subsystem_metrics.redis.Redis')
    @patch('backend.analytics.subsystem_metrics.settings')
    def test_metrics_methods(self, mock_settings, mock_redis):
        mock_settings.SUBSYSTEM_METRICS_REDIS_KEY_PREFIX = 'prefix'
        mock_settings.BROKER_URL = 'redis://'
        mock_settings.CLUSTER_HOST_ID = 'host'
        mock_settings.SUBSYSTEM_METRICS_INTERVAL_SAVE_TO_REDIS = 1
        mock_settings.SUBSYSTEM_METRICS_INTERVAL_SEND_METRICS = 1
        m = Metrics('ns')
        m.set('subsystem_metrics_pipe_execute_seconds', 1.0)
        m.inc('subsystem_metrics_pipe_execute_calls', 1)
        m.decode('subsystem_metrics_pipe_execute_seconds')
        m.load_local_metrics()
        m.serialize_local_metrics()


class TestCustomToPrometheusMetricsCollector(unittest.TestCase):
    @patch('backend.analytics.subsystem_metrics.settings')
    def test_collect(self, mock_settings):
        mock_settings.CLUSTER_HOST_ID = 'host'
        m = MagicMock()
        m.namespace = 'ns'
        m.load_other_metrics.return_value = {'host': {'subsystem_metrics_pipe_execute_seconds': 1}}
        collector = CustomToPrometheusMetricsCollector(m)
        list(collector.collect())


class TestMetricsServerSettings(unittest.TestCase):
    @patch('backend.analytics.subsystem_metrics.settings')
    def test_host_port(self, mock_settings):
        mock_settings.METRICS_SUBSYSTEM_CONFIG = {'server': {'ns': {'port': 1234, 'host': 'localhost'}}}
        ms = MetricsServerSettings('ns')
        self.assertEqual(ms.port(), 1234)
        self.assertEqual(ms.host(), 'localhost')


class TestMetricsServer(unittest.TestCase):
    @patch('backend.analytics.subsystem_metrics.prometheus_client.start_http_server')
    @patch('backend.analytics.subsystem_metrics.settings')
    def test_start(self, mock_settings, mock_start_http_server):
        mock_settings.METRICS_SUBSYSTEM_CONFIG = {'server': {'ns': {'port': 1234, 'host': 'localhost'}}}
        ms = MetricsServer('ns', MagicMock())
        ms.start()
        mock_start_http_server.assert_called()
