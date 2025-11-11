import json
import sys
from datetime import datetime, timezone

import django
import urllib3
from django.conf import settings
from django.core.management.base import BaseCommand

from backend.apps.clusters.models import Cluster, JobLaunchTypeChoices
from backend.apps.scheduler.models import SyncJob, JobTypeChoices


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
                            help='End date for sync (e.g. --until=2025-12-21)')

    def handle(self, *args, **options):

        if not settings.SHOW_URLLIB3_INSECURE_REQUEST_WARNING:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        _since = options.get('since') or None
        _until = options.get('until') or None

        if _since is None or _until is None:
            try:
                confirm = input('Interval not specified. Syncing data may take a long time. Continue Y/N:')
            except EOFError:
                # We get EOFError if "podman run ..." is used without "-it"
                self.stdout.write(self.style.ERROR('\nERROR: Non-iteractive mode, both "since" and "until" options are mandatory.'))
                sys.exit(1)
            if confirm != 'Y':
                sys.exit(1)

        since, until = self.parse_range(_since, _until)

        if since is not None and until is not None and since > until:
            self.stdout.write(self.style.ERROR('Start date is greater than end date'))
            sys.exit(1)

        args = {
            'since': since.isoformat() if since is not None else None,
            'until': until.isoformat() if until is not None else None,
            'managed': True
        }

        job_args = None
        try:
            job_args = json.dumps(args)
        except TypeError as e:
            self.stdout.write(self.style.ERROR('Error parsing arguments: {}'.format(e)))

        try:
            cluster = Cluster.objects.first()
        except django.db.ProgrammingError:
            self.stdout.write(self.style.ERROR('Cluster table does not exist.'))
            sys.exit(1)

        if cluster is None:
            self.stdout.write(self.style.ERROR('Cluster instance does not exist.'))
            sys.exit(1)
        name = "Sync historical data"
        if since is not None:
            name = "{} since {}".format(name, since.isoformat())
        if until is not None:
            name = "{} until {}".format(name, until.isoformat())
        job = SyncJob.objects.create(
            name=name,
            type=JobTypeChoices.SYNC_JOBS,
            launch_type=JobLaunchTypeChoices.MANUAL,
            cluster=cluster,
            job_args=job_args
        )
        job.signal_start()

        self.stdout.write(self.style.SUCCESS(f'Successfully created Sync task for Cluster {cluster}.'))

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
