from ansible_runner.utils.capacity import get_mem_in_bytes, get_cpu_count
from backend.common_utils import get_corrected_memory, get_mem_effective_capacity, get_corrected_cpu, get_cpu_effective_capacity


def get_auto_max_workers():
    """Method we normally rely on to get max_workers

    Uses almost same logic as Instance.local_health_check
    The important thing is to be MORE than Instance.capacity
    so that the task-manager does not over-schedule this node

    Ideally we would just use the capacity from the database plus reserve workers,
    but this poses some bootstrap problems where OCP task containers
    register themselves after startup
    """
    # Get memory from ansible-runner
    total_memory_gb = get_mem_in_bytes()

    # This may replace memory calculation with a user override
    corrected_memory = get_corrected_memory(total_memory_gb)

    # Get same number as max forks based on memory, this function takes memory as bytes
    mem_capacity = get_mem_effective_capacity(corrected_memory, is_control_node=True)

    # Follow same process for CPU capacity constraint
    cpu_count = get_cpu_count()
    corrected_cpu = get_corrected_cpu(cpu_count)
    cpu_capacity = get_cpu_effective_capacity(corrected_cpu, is_control_node=True)

    # Here is what is different from health checks,
    auto_max = max(mem_capacity, cpu_capacity)

    return auto_max
