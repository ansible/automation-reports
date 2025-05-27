import sys
import traceback

import pydantic
import yaml
from django.core.management.base import BaseCommand
from django.db import transaction

from backend.apps.clusters.connector import ApiConnector
from backend.apps.clusters.models import Cluster
from backend.apps.clusters.schemas import ClusterSettings


class Command(BaseCommand):
    help = "Set up AAP instances"

    def add_arguments(self, parser):
        parser.add_argument("path", nargs='+', type=str)

    def handle(self, *args, **options):
        self.stdout.write('Check if table exists.')
        path = options['path'][0] if len(options['path']) == 1 else options['path']
        try:
            db_clusters = {i.address: i for i in Cluster.objects.all()}
        except Exception as ex:
            traceback.print_exc()
            self.stdout.write(self.style.ERROR('Error creating clusters: {}'.format(ex)))
            return
        self.stdout.write('Reading YAML file.')
        try:
            with open(path, 'r') as f:
                try:
                    yaml_settings = yaml.load(f, Loader=yaml.FullLoader)
                except yaml.YAMLError as exc:
                    self.stdout.write(self.style.ERROR('Error while reading yaml file: {}'.format(exc)))
                    return
        except FileNotFoundError as ex:
            self.stdout.write(self.style.ERROR('YAML file not found: {}'.format(path)))
            return

        yaml_clusters = yaml_settings.get('clusters', None)

        if yaml_clusters is None or len(yaml_clusters) == 0:
            self.stdout.write(self.style.ERROR('Improper configured template. Missing key clusters {}.'.format(path)))
            return

        error = False
        with transaction.atomic():
            for cluster in yaml_clusters:
                self.stdout.write(self.style.NOTICE('Adding cluster: address={}'.format(cluster.get("address"))))
                try:
                    new_cluster = ClusterSettings(**cluster)
                except pydantic.ValidationError as ex:
                    self.stdout.write(self.style.ERROR('Error reading new cluster: {}'.format(ex)))
                    transaction.set_rollback(True)
                    error = True
                    break
                db_cluster = db_clusters.pop(new_cluster.address, None)
                new_cluster = Cluster(**new_cluster.model_dump())

                if db_cluster is not None:
                    new_cluster.pk = db_cluster.pk
                    new_cluster.internal_created = db_cluster.internal_created

                new_cluster.save()

                connector = ApiConnector(cluster=Cluster.objects.get(pk=new_cluster.pk))
                try:
                    connector.check_aap_version()
                except Exception as ex:
                    self.stdout.write(self.style.ERROR('Error connecting AAP connector: {}'.format(ex)))
                    transaction.set_rollback(True)
                    error = True
                    break
            for key, value in db_clusters.items():
                value.delete()
        if error:
            sys.exit(1)
        self.stdout.write(self.style.SUCCESS('Successfully set up AAP clusters'))
