import pydantic
import yaml
import traceback
from django.core.management.base import BaseCommand

from backend.apps.clusters.models import Cluster
from backend.apps.clusters.schemas import ClusterSchema
from django.db import transaction


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
                try:
                    new_cluster = ClusterSchema(**cluster)
                except pydantic.ValidationError as ex:
                    self.stdout.write(self.style.ERROR('Error reading new cluster: {}'.format(ex)))
                    transaction.rollback()
                    break
                db_cluster = db_clusters.pop(new_cluster.address, None)
                new_cluster = Cluster(**new_cluster.model_dump())
                if db_cluster is not None:
                    new_cluster.pk = db_cluster.pk

                new_cluster.save()
            for key, value in db_clusters.items():
                value.delete()
        if error:
            return
        self.stdout.write(self.style.SUCCESS('Successfully set up AAP clusters'))
