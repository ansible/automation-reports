from django.contrib import admin

from backend.apps.scheduler.models import SyncSchedule, SyncJob

admin.site.register(SyncSchedule)
admin.site.register(SyncJob)
