import multiprocessing
import os

from backend.common_utils import get_corrected_memory, get_mem_effective_capacity, get_corrected_cpu, get_cpu_effective_capacity

_FALLBACK_MEM_BYTES = 2 * 1024 * 1024 * 1024  # 2 GiB


def _get_mem_in_bytes() -> int:
    """Return total memory in bytes, cgroup-aware.

    Resolution order:
    1. SYSTEM_TASK_ABS_MEM env var (operator override for containers)
    2. cgroup v2 memory.max limit
    3. /proc/meminfo MemTotal
    4. 2 GiB fallback
    """
    override = os.environ.get('SYSTEM_TASK_ABS_MEM')
    if override:
        try:
            return int(override)
        except ValueError:
            pass

    try:
        with open('/sys/fs/cgroup/memory.max') as f:
            val = f.read().strip()
            if val != 'max':
                return int(val)
    except (OSError, ValueError):
        pass

    try:
        with open('/proc/meminfo') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass

    return _FALLBACK_MEM_BYTES


def _get_cpu_count() -> int:
    """Return CPU count, cgroup-aware.

    Resolution order:
    1. SYSTEM_TASK_ABS_CPU env var (operator override for containers)
    2. cgroup v2 cpu.max quota
    3. multiprocessing.cpu_count()
    """
    override = os.environ.get('SYSTEM_TASK_ABS_CPU')
    if override:
        try:
            return int(override)
        except ValueError:
            pass

    try:
        with open('/sys/fs/cgroup/cpu.max') as f:
            quota_str, period_str = f.read().strip().split()
            if quota_str != 'max':
                return max(1, int(int(quota_str) / int(period_str)))
    except (OSError, ValueError, IndexError):
        pass

    return multiprocessing.cpu_count()


def get_auto_max_workers():
    """Method we normally rely on to get max_workers

    Uses almost same logic as Instance.local_health_check
    The important thing is to be MORE than Instance.capacity
    so that the task-manager does not over-schedule this node

    Ideally we would just use the capacity from the database plus reserve workers,
    but this poses some bootstrap problems where OCP task containers
    register themselves after startup
    """
    corrected_memory = get_corrected_memory(_get_mem_in_bytes())
    mem_capacity = get_mem_effective_capacity(corrected_memory, is_control_node=True)

    corrected_cpu = get_corrected_cpu(_get_cpu_count())
    cpu_capacity = get_cpu_effective_capacity(corrected_cpu, is_control_node=True)

    return max(mem_capacity, cpu_capacity)
