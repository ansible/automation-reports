import functools
import logging
import os
import sys
import threading

from django.conf import settings

_task_manager = threading.local()
logger = logging.getLogger('automation_dashboard.utils')


def convert_cpu_str_to_decimal_cpu(cpu_str):
    """Convert a string indicating cpu units to decimal.

    Useful for dealing with cpu setting that may be expressed in units compatible with
    kubernetes.

    See https://kubernetes.io/docs/tasks/configure-pod-container/assign-cpu-resource/#cpu-units
    """
    cpu = cpu_str
    millicores = False

    if cpu_str[-1] == 'm':
        cpu = cpu_str[:-1]
        millicores = True

    try:
        cpu = float(cpu)
    except ValueError:
        cpu = 1.0
        millicores = False
        logger.warning(
            f"Could not convert SYSTEM_TASK_ABS_CPU {cpu_str} to a decimal number, falling back to default of 1 cpu")

    if millicores:
        cpu = cpu / 1000

    # Per kubernetes docs, fractional CPU less than .1 are not allowed
    return max(0.1, round(cpu, 1))


def get_corrected_cpu(cpu_count):  # formerlly get_cpu_capacity
    """Some environments will do a correction to the reported CPU number
    because the given OpenShift value is a lie
    """
    settings_abscpu = getattr(settings, 'SYSTEM_TASK_ABS_CPU', None)
    env_abscpu = os.getenv('SYSTEM_TASK_ABS_CPU', None)

    if env_abscpu is not None:
        return convert_cpu_str_to_decimal_cpu(env_abscpu)
    elif settings_abscpu is not None:
        return convert_cpu_str_to_decimal_cpu(settings_abscpu)

    return cpu_count  # no correction


def convert_mem_str_to_bytes(mem_str):
    """Convert string with suffix indicating units to memory in bytes (base 2)

    Useful for dealing with memory setting that may be expressed in units compatible with
    kubernetes.

    See https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory
    """
    # If there is no suffix, the memory sourced from the request is in bytes
    if mem_str.isdigit():
        return int(mem_str)

    conversions = {
        'Ei': lambda x: x * 2 ** 60,
        'E': lambda x: x * 10 ** 18,
        'Pi': lambda x: x * 2 ** 50,
        'P': lambda x: x * 10 ** 15,
        'Ti': lambda x: x * 2 ** 40,
        'T': lambda x: x * 10 ** 12,
        'Gi': lambda x: x * 2 ** 30,
        'G': lambda x: x * 10 ** 9,
        'Mi': lambda x: x * 2 ** 20,
        'M': lambda x: x * 10 ** 6,
        'Ki': lambda x: x * 2 ** 10,
        'K': lambda x: x * 10 ** 3,
    }
    mem = 0
    mem_unit = None
    for i, char in enumerate(mem_str):
        if not char.isdigit():
            mem_unit = mem_str[i:]
            mem = int(mem_str[:i])
            break
    if not mem_unit or mem_unit not in conversions.keys():
        error = f"Unsupported value for SYSTEM_TASK_ABS_MEM: {mem_str}, memory must be expressed in bytes or with known suffix: {conversions.keys()}. Falling back to 1 byte"
        logger.warning(error)
        return 1
    return max(1, conversions[mem_unit](mem))


def get_corrected_memory(memory):
    settings_absmem = getattr(settings, 'SYSTEM_TASK_ABS_MEM', None)
    env_absmem = os.getenv('SYSTEM_TASK_ABS_MEM', None)

    # Runner returns memory in bytes
    # so we convert memory from settings to bytes as well.

    if env_absmem is not None:
        return convert_mem_str_to_bytes(env_absmem)
    elif settings_absmem is not None:
        return convert_mem_str_to_bytes(settings_absmem)

    return memory


def get_mem_effective_capacity(mem_bytes, is_control_node=False):
    settings_mem_mb_per_fork = getattr(settings, 'SYSTEM_TASK_FORKS_MEM', None)
    env_mem_mb_per_fork = os.getenv('SYSTEM_TASK_FORKS_MEM', None)
    if is_control_node:
        mem_bytes = get_corrected_memory(mem_bytes)
    if env_mem_mb_per_fork:
        mem_mb_per_fork = int(env_mem_mb_per_fork)
    elif settings_mem_mb_per_fork:
        mem_mb_per_fork = int(settings_mem_mb_per_fork)
    else:
        mem_mb_per_fork = 100

    # Per docs, deduct 2GB of memory from the available memory
    # to cover memory consumption of background tasks when redis/web etc are colocated with
    # the other control processes
    memory_penalty_bytes = 2147483648
    if settings.IS_K8S:
        # In k8s, this is dealt with differently because
        # redis and the web containers have their own memory allocation
        memory_penalty_bytes = 0

    # convert memory to megabytes because our setting of how much memory we
    # should allocate per fork is in megabytes
    mem_mb = (mem_bytes - memory_penalty_bytes) // 2 ** 20
    max_forks_based_on_memory = mem_mb // mem_mb_per_fork

    return max(1, max_forks_based_on_memory)


def get_cpu_effective_capacity(cpu_count, is_control_node=False):
    settings_forkcpu = getattr(settings, 'SYSTEM_TASK_FORKS_CPU', None)
    env_forkcpu = os.getenv('SYSTEM_TASK_FORKS_CPU', None)
    if is_control_node:
        cpu_count = get_corrected_cpu(cpu_count)
    if env_forkcpu:
        forkcpu = int(env_forkcpu)
    elif settings_forkcpu:
        forkcpu = int(settings_forkcpu)
    else:
        forkcpu = 4

    return max(1, int(cpu_count * forkcpu))


@functools.cache
def is_testing(argv=None):
    '''Return True if running django or py.test unit tests.'''
    if os.environ.get('DJANGO_SETTINGS_MODULE') == 'backend.tests.settings_for_test':
        return True
    argv = sys.argv if argv is None else argv
    if len(argv) >= 1 and ('py.test' in argv[0] or 'py/test.py' in argv[0]):
        return True
    elif len(argv) >= 2 and argv[1] == 'test':
        return True
    return False


class ScheduleSyncManager:
    def __init__(self, manager, manager_threading_local):
        self.manager = manager
        self.manager_threading_local = manager_threading_local

    def _schedule(self):
        from django.db import connection

        # runs right away if not in transaction
        connection.on_commit(lambda: self.manager.delay())

    def schedule(self):
        if getattr(self.manager_threading_local, 'bulk_reschedule', False):
            self.manager_threading_local.needs_scheduling = True
            return
        self._schedule()


class ScheduleSyncTaskManager(ScheduleSyncManager):
    def __init__(self):
        from backend.apps.scheduler.tasks import sync_task_manager
        super().__init__(sync_task_manager, _task_manager)
