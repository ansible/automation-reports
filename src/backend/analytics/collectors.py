from django.db.models import Count

from backend.apps.scheduler.models import SyncJob


def job_counts():
    counts = {
        'total_jobs': SyncJob.objects.count(),
        'status': dict(SyncJob.objects.values_list('status').annotate(Count('status')).order_by()),
        'launch_type': dict(SyncJob.objects.values_list('launch_type').annotate(Count('launch_type')).order_by()),
        'type': dict(SyncJob.objects.values_list('type').annotate(Count('type')).order_by())}
    return counts
