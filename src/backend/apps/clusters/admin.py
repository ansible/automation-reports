from django.contrib import admin

from backend.apps.clusters.models import (
    Cluster,
    ClusterSyncStatus,
    ClusterSyncData,
    Organization,
    JobTemplate,
    AAPUser,
    Inventory,
    ExecutionEnvironment,
    InstanceGroup,
    Label,
    Job,
    JobLabel,
    Host,
    JobHostSummary,
    Project
    )

admin.site.register(Cluster)
admin.site.register(ClusterSyncStatus)
admin.site.register(ClusterSyncData)
admin.site.register(Organization)
admin.site.register(JobTemplate)
admin.site.register(AAPUser)
admin.site.register(Inventory)
admin.site.register(ExecutionEnvironment)
admin.site.register(InstanceGroup)
admin.site.register(Label)
admin.site.register(Job)
admin.site.register(JobLabel)
admin.site.register(Host)
admin.site.register(JobHostSummary)
admin.site.register(Project)
