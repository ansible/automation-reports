import pydantic
import yaml
from django.core.management.base import BaseCommand

from backend.apps.instances.models import Instance
from backend.apps.instances.schemas import InstanceSchema
from django.db import transaction


class Command(BaseCommand):
    help = "Set up AAP instances"

    def add_arguments(self, parser):
        parser.add_argument("path", nargs='+', type=str)

    def handle(self, *args, **options):
        self.stdout.write('Check if table exists.')
        path = options['path'][0] if len(options['path']) == 1 else options['path']
        try:
            db_instances = {i.host: i for i in Instance.objects.all()}
        except Exception as ex:
            self.stdout.write(self.style.ERROR('Error creating instances: {}'.format(ex)))
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

        yaml_instances = yaml_settings.get('instances', None)

        if yaml_instances is None or len(yaml_instances) == 0:
            self.stdout.write(self.style.ERROR('Improper configured template. Missing key instances {}.'.format(path)))

        error = False
        with transaction.atomic():
            for instance in yaml_instances:
                try:
                    new_instance = InstanceSchema(**instance)
                except pydantic.ValidationError as ex:
                    self.stdout.write(self.style.ERROR('Error reading new instance: {}'.format(ex)))
                    transaction.rollback()
                    break
                db_instance = db_instances.pop(new_instance.host, None)
                new_instance = Instance(**new_instance.model_dump())
                if db_instance is not None:
                    new_instance.pk = db_instance.pk

                new_instance.save()
            for key, value in db_instances.items():
                value.delete()
        if error:
            return
        self.stdout.write(self.style.SUCCESS('Successfully set up AAP instances'))
