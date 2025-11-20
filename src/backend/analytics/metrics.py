from prometheus_client import CollectorRegistry, Gauge, generate_latest

from backend.analytics.collectors import job_counts
from backend.apps.clusters.models import JobStatusChoices
from backend.apps.scheduler.models import JobTypeChoices


def metrics():
    registry = CollectorRegistry()

    all_jobs = Gauge(
        'automation_dashboard_jobs_total',
        'Number of all jobs on the system',
        registry=registry)

    jobs_by_status = Gauge(
        'automation_dashboard_status_total',
        'Status of Job launched',
        [
            'status',
        ],
        registry=registry,
    )

    jobs_by_type = Gauge(
        'automation_dashboard_type_total',
        'Type of Job launched',
        [
            'type',
        ],
        registry=registry,
    )

    all_job_data = job_counts()
    job_count_by_status = all_job_data.get('status', {})
    states = set(dict(JobStatusChoices.choices)) - {JobStatusChoices.NEW}
    for state in states:
        jobs_by_status.labels(status=state).set(job_count_by_status.get(state, 0))

    all_jobs.set(all_job_data.get('total_jobs', {}))

    job_types = set(dict(JobTypeChoices.choices))
    job_count_by_type = all_job_data.get('type', {})
    for job_type in job_types:
        jobs_by_type.labels(type=job_type).set(job_count_by_type.get(job_type, 0))

    return generate_latest(registry=registry)
