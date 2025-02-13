from django.core.management.base import BaseCommand

from backend.apps.clusters.models import (
    Cluster,
    ClusterSyncData,
    ClusterSyncStatus,
    Organization,
    JobTemplate,
    AAPUser,
    Inventory,
    ExecutionEnvironment,
    InstanceGroup,
    Label,
    Host,
    Job,
    JobLabel,
    JobHostSummary)


class Command(BaseCommand):
    help = "Clear db"

    def handle(self, *args, **options):
        confirm = input('This will delete all data from data base. Are you sure? Y/n:')
        if confirm != 'Y':
            return
        print("Clearing db")
        Cluster.objects.all().delete()
        ClusterSyncData.objects.all().delete()
        ClusterSyncStatus.objects.all().delete()
        Organization.objects.all().delete()
        JobTemplate.objects.all().delete()
        AAPUser.objects.all().delete()
        Inventory.objects.all().delete()
        ExecutionEnvironment.objects.all().delete()
        InstanceGroup.objects.all().delete()
        Label.objects.all().delete()
        Host.objects.all().delete()
        Job.objects.all().delete()
        JobLabel.objects.all().delete()
        JobHostSummary.objects.all().delete()
        print("DB cleared")
