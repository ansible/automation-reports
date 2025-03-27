from datetime import datetime, timezone

import urllib3
from django.conf import settings
from django.core.management.base import BaseCommand

from backend.apps.clusters.connector import ApiConnector
from backend.apps.clusters.models import Cluster, ClusterSyncData
from backend.apps.clusters.parser import DataParser


class Command(BaseCommand):
    help = "Sync AAP instances data"

    def add_arguments(self, parser):
        parser.add_argument('--since',
                            dest='since',
                            action='store',
                            help='Start date for sync (e.g. --since=2025-01-20)')

        parser.add_argument('--until',
                            dest='until',
                            action='store',
                            help='End date for  sync (e.g. --until=2025-12-21)')

    def handle(self, *args, **options):

        if not settings.SHOW_URLLIB3_INSECURE_REQUEST_WARNING:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        _since = options.get('since') or None
        _until = options.get('until') or None

        if _since is None or _until is None:
            confirm = input('Interval not specified. Syncing data may take a long time. Continue Y/N:')
            if confirm != 'Y':
                return

        since, until = self.parse_range(_since, _until)

        if since is not None and until is not None and since > until:
            self.stdout.write(self.style.ERROR('Start date is greater than end date'))
            return

        self.stdout.write('Check if cluster table exists.')

        try:
            Cluster.objects.first()
        except:
            self.stdout.write(self.style.ERROR('Cluster table does not exist.'))
            return

        clusters = Cluster.objects.all()
        if clusters.count() == 0:
            self.stdout.write(self.style.ERROR('No clusters found.'))

        for cluster in clusters:
            connector = ApiConnector(
                cluster=cluster,
                since=since,
                until=until,
                managed=True
            )
            try:
                self.stdout.write(f'Start syncing cluster {cluster}.')
                connector.sync()
                self.stdout.write(self.style.SUCCESS(f'Cluster {cluster} synced.'))
            except Exception as e:
                print(e)

        data = ClusterSyncData.objects.all()
        for sync_data in data:
            try:
                self.stdout.write(f'Start parsing job {sync_data.id}.')
                parser = DataParser(sync_data.id)
                parser.parse()
                self.stdout.write(self.style.SUCCESS(f'Job with id {sync_data.id} parsed.'))
            except Exception as e:
                print(e)

    def parse_range(self, _since, _until):
        since = self.parse_date(_since) if _since else None
        until = self.parse_date(_until, True) if _until else None

        return since, until

    def parse_date(self, date_string, end=False):
        tmp = date_string.split('T')
        d = datetime.fromisoformat(date_string)
        if d:
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            else:
                d = d.astimezone(timezone.utc)
        if len(tmp) == 1:
            if end:
                d = datetime.combine(d, datetime.max.time(), tzinfo=timezone.utc)
            else:
                d = datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc)
        return d
