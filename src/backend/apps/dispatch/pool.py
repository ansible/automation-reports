import multiprocessing

from backend.common_utils import get_corrected_memory, get_mem_effective_capacity, get_corrected_cpu, get_cpu_effective_capacity


def _get_mem_in_bytes() -> int:
    """Return total physical memory in bytes, read from /proc/meminfo on Linux."""
    try:
        with open('/proc/meminfo') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    return int(line.split()[1]) * 1024
    except (FileNotFoundError, ValueError, IndexError):
        pass
    return 2 * 1024 * 1024 * 1024


def get_auto_max_workers():
    """Method we normally rely on to get max_workers

    Uses almost same logic as Instance.local_health_check
    The important thing is to be MORE than Instance.capacity
    so that the task-manager does not over-schedule this node

    Ideally we would just use the capacity from the database plus reserve workers,
    but this poses some bootstrap problems where OCP task containers
    register themselves after startup
    """
    total_memory_gb = _get_mem_in_bytes()
    corrected_memory = get_corrected_memory(total_memory_gb)
    mem_capacity = get_mem_effective_capacity(corrected_memory, is_control_node=True)

    cpu_count = multiprocessing.cpu_count()
    corrected_cpu = get_corrected_cpu(cpu_count)
    cpu_capacity = get_cpu_effective_capacity(corrected_cpu, is_control_node=True)

    auto_max = max(mem_capacity, cpu_capacity)

    return auto_max
