import sys

import yaml
from django.core.management.base import BaseCommand
from django.template.backends import django

from backend.apps.clusters.encryption import decrypt_value
from backend.apps.clusters.models import Cluster
from backend.apps.scheduler.models import SyncSchedule as SyncScheduleModel


class Command(BaseCommand):
    help = "Get AAP instances"

    def add_arguments(self, parser):
        parser.add_argument(
            "--decrypt", action='store_true', default=False,
            help="Show also decrypted token values.",
            )

    def handle(self, *args, **options):
        # self.stdout.write('Check if table exists.')
        try:
            db_clusters = {i.address: i for i in Cluster.objects.all()}
        except django.db.ProgrammingError:
            self.stdout.write(self.style.ERROR('Cluster table does not exist.'))
            sys.exit(1)

        cluster_attrs_plaintext = ["protocol", "address", "port", "client_id", "verify_ssl"]
        cluster_attrs_encrypted = ["access_token", "refresh_token", "client_secret"]
        sync_attrs = ["name", "rrule", "enabled"]
        clusters_list = []
        for cluster in Cluster.objects.all():
            cluster_dict = {kk: getattr(cluster, kk) for kk in cluster_attrs_plaintext}
            if options['decrypt']:
                cluster_dict.update({kk: decrypt_value(getattr(cluster, kk)) for kk in cluster_attrs_encrypted})
            cluster_dict["sync_schedules"] = []
            for sync_setting in SyncScheduleModel.objects.filter(cluster=cluster):
                sync_setting_dict = {kk: getattr(sync_setting, kk) for kk in sync_attrs}
                cluster_dict["sync_schedules"].append(sync_setting_dict)
            clusters_list.append(cluster_dict)

        doc = dict(clusters=clusters_list)
        msg = yaml.dump(doc, indent=4)
        self.stdout.write(msg)
