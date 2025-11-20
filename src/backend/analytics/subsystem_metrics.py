import itertools
import json
import logging
import time

import prometheus_client
import redis
from django.conf import settings
from django.http import HttpRequest
from prometheus_client.metrics_core import GaugeMetricFamily, HistogramMetricFamily
from prometheus_client.registry import CollectorRegistry
from rest_framework.request import Request

from backend.common_utils import is_testing

logger = logging.getLogger('automation_dashboard.analytics')
root_key = settings.SUBSYSTEM_METRICS_REDIS_KEY_PREFIX


class BaseM:
    def __init__(self, field, help_text, labels=None):
        self.field = field
        self.help_text = help_text
        self.current_value = 0
        self.metric_has_changed = False
        self.labels = labels or {}

    def reset_value(self, conn):
        conn.hset(root_key, self.field, 0)
        self.current_value = 0

    def inc(self, value):
        self.current_value += value
        self.metric_has_changed = True

    def set(self, value):
        self.current_value = value
        self.metric_has_changed = True

    def get(self):
        return self.current_value

    def decode_value(self, value):
        return value

    def decode(self, conn):
        value = conn.hget(root_key, self.field)
        return self.decode_value(value)

    def to_prometheus(self, instance_data, namespace=None):
        output_text = f"# HELP {self.field} {self.help_text}\n# TYPE {self.field} gauge\n"
        for instance in instance_data:
            if self.field in instance_data[instance]:
                # Build label string
                labels = f'node="{instance}"'
                if namespace:
                    labels += f',subsystem="{namespace}"'
                # on upgrade, if there are stale instances, we can end up with issues where new metrics are not present
                output_text += f'{self.field}{{{labels}}} {instance_data[instance][self.field]}\n'
        return output_text


class FloatM(BaseM):
    def decode_value(self, value):
        if value is not None:
            return float(value)
        else:
            return 0.0

    def store_value(self, conn):
        if self.metric_has_changed:
            conn.hincrbyfloat(root_key, self.field, self.current_value)
            self.current_value = 0
            self.metric_has_changed = False

    class IntM(BaseM):
        def decode_value(self, value):
            if value is not None:
                return int(value)
            else:
                return 0

        def store_value(self, conn):
            if self.metric_has_changed:
                conn.hincrby(root_key, self.field, self.current_value)
                self.current_value = 0
                self.metric_has_changed = False


class IntM(BaseM):
    def decode_value(self, value):
        if value is not None:
            return int(value)
        else:
            return 0

    def store_value(self, conn):
        if self.metric_has_changed:
            conn.hincrby(root_key, self.field, self.current_value)
            self.current_value = 0
            self.metric_has_changed = False


class SetIntM(BaseM):
    def decode_value(self, value):
        if value is not None:
            return int(value)
        else:
            return 0

    def store_value(self, conn):
        if self.metric_has_changed:
            conn.hset(root_key, self.field, self.current_value)
            self.metric_has_changed = False


class SetFloatM(SetIntM):
    def decode_value(self, value):
        if value is not None:
            return float(value)
        else:
            return 0


class HistogramM(BaseM):
    def __init__(self, field, help_text, buckets):
        self.buckets = buckets
        self.buckets_to_keys = {}
        for b in buckets:
            self.buckets_to_keys[b] = IntM(field + '_' + str(b), '')
        self.inf = IntM(field + '_inf', '')
        self.sum = IntM(field + '_sum', '')
        super(HistogramM, self).__init__(field, help_text)

    def reset_value(self, conn):
        conn.hset(root_key, self.field, 0)
        self.inf.reset_value(conn)
        self.sum.reset_value(conn)
        for b in self.buckets_to_keys.values():
            b.reset_value(conn)
        super(HistogramM, self).reset_value(conn)

    def observe(self, value):
        for b in self.buckets:
            if value <= b:
                self.buckets_to_keys[b].inc(1)
                break
        self.sum.inc(value)
        self.inf.inc(1)

    def decode(self, conn):
        values = {'counts': []}
        for b in self.buckets_to_keys:
            values['counts'].append(self.buckets_to_keys[b].decode(conn))
        values['sum'] = self.sum.decode(conn)
        values['inf'] = self.inf.decode(conn)
        return values

    def store_value(self, conn):
        for b in self.buckets:
            self.buckets_to_keys[b].store_value(conn)
        self.sum.store_value(conn)
        self.inf.store_value(conn)

    def to_prometheus(self, instance_data, namespace=None):
        output_text = f"# HELP {self.field} {self.help_text}\n# TYPE {self.field} histogram\n"
        for instance in instance_data:
            # Build label string
            node_label = f'node="{instance}"'
            subsystem_label = f',subsystem="{namespace}"' if namespace else ''
            for i, b in enumerate(self.buckets):
                output_text += f'{self.field}_bucket{{le="{b}",{node_label}{subsystem_label}}} {sum(instance_data[instance][self.field]["counts"][0:i + 1])}\n'
            output_text += f'{self.field}_bucket{{le="+Inf",{node_label}{subsystem_label}}} {instance_data[instance][self.field]["inf"]}\n'
            output_text += f'{self.field}_count{{{node_label}{subsystem_label}}} {instance_data[instance][self.field]["inf"]}\n'
            output_text += f'{self.field}_sum{{{node_label}{subsystem_label}}} {instance_data[instance][self.field]["sum"]}\n'
        return output_text


class MetricsNamespace:
    def __init__(self, namespace):
        self.namespace = namespace


class Metrics(MetricsNamespace):
    METRICS_LIST = []
    _METRICS_LIST = [
        FloatM('subsystem_metrics_pipe_execute_seconds', 'Time spent saving metrics to redis'),
        IntM('subsystem_metrics_pipe_execute_calls', 'Number of calls to pipe_execute'),
        FloatM('subsystem_metrics_send_metrics_seconds', 'Time spent sending metrics to other nodes'),
    ]

    def __init__(self, namespace, auto_pipe_execute=False, instance_name=None, metrics_have_changed=True, **kwargs):
        MetricsNamespace.__init__(self, namespace)
        self.pipe = redis.Redis.from_url(settings.BROKER_URL).pipeline()
        self.conn = redis.Redis.from_url(settings.BROKER_URL)
        self.last_pipe_execute = time.time()
        self.auto_pipe_execute = auto_pipe_execute
        self.metrics_have_changed = metrics_have_changed
        self.pipe_execute_interval = settings.SUBSYSTEM_METRICS_INTERVAL_SAVE_TO_REDIS
        self.send_metrics_interval = settings.SUBSYSTEM_METRICS_INTERVAL_SEND_METRICS

        if instance_name:
            self.instance_name = instance_name
        elif is_testing():
            self.instance_name = "awx_testing"
        else:
            self.instance_name = settings.CLUSTER_HOST_ID

        self.METRICS = {}
        for m in itertools.chain(self.METRICS_LIST, self._METRICS_LIST):
            self.METRICS[m.field] = m

        # track last time metrics were sent to other nodes
        self.previous_send_metrics = SetFloatM('send_metrics_time', 'Timestamp of previous send_metrics call')

    def observe(self, field, value):
        self.METRICS[field].observe(value)
        self.metrics_have_changed = True
        if self.auto_pipe_execute:
            self.pipe_execute()

    def reset_values(self):
        # intended to be called once on app startup to reset all metric
        # values to 0
        for m in self.METRICS.values():
            m.reset_value(self.conn)
        self.metrics_have_changed = True
        self.conn.delete(root_key + "_lock")
        for m in self.conn.scan_iter(root_key + '-' + self.namespace + '_instance_*'):
            self.conn.delete(m)

    def set(self, field, value):
        self.METRICS[field].set(value)
        self.metrics_have_changed = True
        if self.auto_pipe_execute:
            self.pipe_execute()

    def inc(self, field, value):
        if value != 0:
            self.METRICS[field].inc(value)
            self.metrics_have_changed = True
            if self.auto_pipe_execute:
                self.pipe_execute()

    def decode(self, field):
        return self.METRICS[field].decode(self.conn)

    def load_local_metrics(self):
        # generate python dictionary of key values from metrics stored in redis
        data = {}
        for field in self.METRICS:
            data[field] = self.METRICS[field].decode(self.conn)
        return data

    def serialize_local_metrics(self):
        data = self.load_local_metrics()
        return json.dumps(data)

    def pipe_execute(self):
        if self.metrics_have_changed:
            duration_pipe_exec = time.perf_counter()
            for m in self.METRICS:
                self.METRICS[m].store_value(self.pipe)
            self.pipe.execute()
            self.last_pipe_execute = time.time()
            self.metrics_have_changed = False
            duration_pipe_exec = time.perf_counter() - duration_pipe_exec

            duration_send_metrics = time.perf_counter()
            self.send_metrics()
            duration_send_metrics = time.perf_counter() - duration_send_metrics

            # Increment operational metrics
            self.METRICS['subsystem_metrics_pipe_execute_seconds'].inc(duration_pipe_exec)
            self.METRICS['subsystem_metrics_pipe_execute_calls'].inc(1)
            self.METRICS['subsystem_metrics_send_metrics_seconds'].inc(duration_send_metrics)

    def send_metrics(self):
        # more than one thread could be calling this at the same time, so should
        # acquire redis lock before sending metrics
        try:
            lock = self.conn.lock(root_key + '-' + self.namespace + '_lock')
            if not lock.acquire(blocking=False):
                return
        except redis.exceptions.ConnectionError as exc:
            logger.warning(f'Connection error in send_metrics: {exc}')
            return
        try:
            current_time = time.time()
            if current_time - self.previous_send_metrics.decode(self.conn) > self.send_metrics_interval:
                serialized_metrics = self.serialize_local_metrics()
                self.conn.set(root_key + '-' + self.namespace + '_instance_' + self.instance_name, serialized_metrics)
                self.previous_send_metrics.set(current_time)
                self.previous_send_metrics.store_value(self.conn)
        finally:
            try:
                lock.release()
            except Exception as exc:
                # After system failures, we might throw redis.exceptions.LockNotOwnedError
                # this is to avoid print a Traceback, and importantly, avoid raising an exception into parent context
                logger.warning(f'Error releasing subsystem metrics redis lock, error: {str(exc)}')

    def load_other_metrics(self, request):
        # data received from other nodes are stored in their own keys
        # e.g., awx_metrics_instance_awx-1, awx_metrics_instance_awx-2
        # this method looks for keys with "_instance_" in the name and loads the data
        # also filters data based on request query params
        # if additional filtering is added, update metrics_view.md
        instances_filter = request.GET.getlist("node")
        # get a sorted list of instance names
        instance_names = [self.instance_name]
        for m in self.conn.scan_iter(root_key + '-' + self.namespace + '_instance_*'):
            instance_names.append(m.decode('UTF-8').split('_instance_')[1])
        instance_names.sort()
        # load data, including data from the local instance
        instance_data = {}
        for instance in instance_names:
            if len(instances_filter) == 0 or instance in instances_filter:
                instance_data_from_redis = self.conn.get(root_key + '-' + self.namespace + '_instance_' + instance)
                # data from other instances may not be available. That is OK.
                if instance_data_from_redis:
                    instance_data[instance] = json.loads(instance_data_from_redis.decode('UTF-8'))
        return instance_data

    def generate_metrics(self, request):
        # takes the api request, filters, and generates prometheus data
        # if additional filtering is added, update metrics_view.md
        instance_data = self.load_other_metrics(request)
        metrics_filter = request.GET.getlist("metric")
        output_text = ''
        if instance_data:
            for field in self.METRICS:
                if len(metrics_filter) == 0 or field in metrics_filter:
                    # Add subsystem label only for operational metrics
                    namespace = (
                        self.namespace
                        if field in ['subsystem_metrics_pipe_execute_seconds', 'subsystem_metrics_pipe_execute_calls',
                                     'subsystem_metrics_send_metrics_seconds']
                        else None
                    )
                    output_text += self.METRICS[field].to_prometheus(instance_data, namespace)
        return output_text


class DispatcherMetrics(Metrics):
    METRICS_LIST = [
        SetFloatM('automation_dashboard_task_manager_recorded_timestamp',
                  'Unix timestamp when metrics were last recorded'),
        SetFloatM('automation_dashboard_task_manager_get_tasks_seconds', 'Time spent in loading tasks from db'),
        SetFloatM('automation_dashboard_task_manager_commit_seconds',
                  'Time spent in db transaction, including on_commit calls'),
        SetIntM('automation_dashboard_task_manager_tasks_started', 'Number of tasks started'),
        SetFloatM('automation_dashboard_task_manager_start_task_seconds', 'Time spent starting task'),
        SetFloatM('automation_dashboard_task_manager_process_pending_tasks_seconds',
                  'Time spent processing pending tasks'),
        SetIntM('automation_dashboard_task_manager_running_processed', 'Number of running tasks processed'),
        SetIntM('automation_dashboard_task_manager_pending_processed', 'Number of pending tasks processed'),
        IntM('automation_dashboard_task_manager__schedule_calls',
             'Number of calls to _schedule, after lock is acquired'),

        SetIntM('automation_dashboard_parse_job_tasks_started', 'Number of running parse job tasks'),
        SetIntM('automation_dashboard_parse_job_tasks_succeeded', 'Number of succeeded parse job tasks'),
        SetIntM('automation_dashboard_parse_job_tasks_failed', 'Number of failed parse job tasks'),
        SetFloatM('automation_dashboard_parse_job_tasks_duration_seconds',
                  'Time spent in executing parse job tasks'),

        SetIntM('automation_dashboard_sync_job_tasks_started', 'Number of running sync job tasks'),
        SetIntM('automation_dashboard_sync_job_tasks_succeeded', 'Number of succeeded sync job tasks'),
        SetIntM('automation_dashboard_sync_job_tasks_failed', 'Number of failed sync job tasks'),
        SetFloatM('automation_dashboard_sync_job_tasks_duration_seconds',
                  'Time spent in executing sync job tasks'),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(settings.METRICS_SERVICE_DISPATCHER, *args, **kwargs)


class CustomToPrometheusMetricsCollector(prometheus_client.registry.Collector):

    def __init__(self, metrics_obj, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._metrics = metrics_obj

    def collect(self):
        my_hostname = settings.CLUSTER_HOST_ID
        instance_data = self._metrics.load_other_metrics(Request(HttpRequest()))

        if not instance_data:
            logger.debug(f"No metric data not found in redis for metric namespace '{self._metrics.namespace}'")
            return None

        if not (host_metrics := instance_data.get(my_hostname)):
            logger.debug(
                f"Metric data for this node '{my_hostname}' not found in redis for metric namespace '{self._metrics.namespace}'")
            return None

        for _, metric in self._metrics.METRICS.items():
            entry = host_metrics.get(metric.field)
            if not entry:
                logger.debug(
                    f"{self._metrics.namespace} metric '{metric.field}' not found in redis data payload {json.dumps(instance_data, indent=2)}")
                continue
            if isinstance(metric, HistogramM):
                buckets = list(zip(metric.buckets, entry['counts']))
                buckets = [[str(i[0]), str(i[1])] for i in buckets]
                yield HistogramMetricFamily(metric.field, metric.help_text, buckets=buckets, sum_value=entry['sum'])
            else:
                yield GaugeMetricFamily(metric.field, metric.help_text, value=entry)
        return None


class MetricsServerSettings(MetricsNamespace):
    def port(self):
        return settings.METRICS_SUBSYSTEM_CONFIG['server'][self.namespace]['port']

    def host(self):
        return settings.METRICS_SUBSYSTEM_CONFIG['server'][self.namespace]['host']


class MetricsServer(MetricsServerSettings):
    def __init__(self, namespace, registry):
        MetricsNamespace.__init__(self, namespace)
        self._registry = registry

    def start(self):
        try:
            prometheus_client.start_http_server(self.port(), addr=self.host(), registry=self._registry)
            logger.info(f'Starting dispatcherd prometheus server.')
            logger.info(f'Prometheus server running on http://{self.host()}:{self.port()}.')
        except Exception:
            logger.error(f'MetricsServer failed to start for service {self.namespace}.')
            raise


class DispatcherMetricsServer(MetricsServer):
    def __init__(self):
        registry = CollectorRegistry(auto_describe=True)
        registry.register(CustomToPrometheusMetricsCollector(DispatcherMetrics(metrics_have_changed=False)))
        super().__init__(settings.METRICS_SERVICE_DISPATCHER, registry)


def metrics(request):
    output_text = ''
    m = DispatcherMetrics()

    output_text += m.generate_metrics(request)
    return output_text
