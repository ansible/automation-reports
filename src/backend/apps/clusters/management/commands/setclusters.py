import os
import re
import sys

import pydantic
import yaml
from dateutil.rrule import rrulestr
from django.core.management.base import BaseCommand
from django.db import transaction
from django.template.backends import django
from django.utils.translation import gettext_lazy as _

from backend.apps.clusters.connector import ApiConnector
from backend.apps.clusters.encryption import encrypt_value
from backend.apps.clusters.models import Cluster
from backend.apps.clusters.schemas import ClusterSettings
from backend.apps.scheduler.models import SyncSchedule as SyncScheduleModel


def validate_rrule(value):
    rrule_value = value
    by_day_with_numeric_prefix = r".*?BYDAY[\:\=][0-9]+[a-zA-Z]{2}"
    match_multiple_dtstart = re.findall(r".*?(DTSTART(;[^:]+)?\:[0-9]+T[0-9]+Z?)", rrule_value)
    match_native_dtstart = re.findall(r".*?(DTSTART:[0-9]+T[0-9]+) ", rrule_value)
    match_multiple_rrule = re.findall(r".*?(RULE\:[^\s]*)", rrule_value)
    errors = []
    if not len(match_multiple_dtstart):
        errors.append(_('Valid DTSTART required in rrule. Value should start with: DTSTART:YYYYMMDDTHHMMSSZ'))
    if len(match_native_dtstart):
        errors.append(_('DTSTART cannot be a naive datetime.  Specify ;TZINFO= or YYYYMMDDTHHMMSSZZ.'))
    if len(match_multiple_dtstart) > 1:
        errors.append(_('Multiple DTSTART is not supported.'))
    if "exdate:" in rrule_value.lower():
        errors.append(_('EXDATE not allowed in rrule.'))
    if "rdate:" in rrule_value.lower():
        errors.append(_('RDATE not allowed in rrule.'))
    for a_rule in match_multiple_rrule:
        if 'interval' not in a_rule.lower():
            errors.append("{0}: {1}".format(_('INTERVAL required in rrule'), a_rule))
        elif 'secondly' in a_rule.lower():
            errors.append("{0}: {1}".format(_('SECONDLY is not supported'), a_rule))
        if re.match(by_day_with_numeric_prefix, a_rule):
            errors.append("{0}: {1}".format(_("BYDAY with numeric prefix not supported"), a_rule))
        if 'COUNT' in a_rule and 'UNTIL' in a_rule:
            errors.append("{0}: {1}".format(_("RRULE may not contain both COUNT and UNTIL"), a_rule))
        match_count = re.match(r".*?(COUNT\=[0-9]+)", a_rule)
        if match_count:
            count_val = match_count.groups()[0].strip().split("=")
            if int(count_val[1]) > 999:
                errors.append("{0}: {1}".format(_("COUNT > 999 is unsupported"), a_rule))

    try:
        SyncScheduleModel.rrulestr(rrule_value)
    except Exception as e:
        import traceback

        errors.append(_("rrule parsing failed validation: {}").format(e))

    return errors if len(errors) > 0 else None


class Command(BaseCommand):
    help = "Set up AAP instances"

    def add_arguments(self, parser):
        parser.add_argument("--keep", action="store_true", help="Keep (do not remove) the clusters.yaml after processing")
        parser.add_argument("path", nargs='+', type=str, help="Path to the clusters.yaml file")

    def handle(self, *args, **options):
        self.stdout.write('Check if table exists.')
        path = options['path'][0] if len(options['path']) == 1 else options['path']
        keep_file = options['keep']
        try:
            db_clusters = {i.address: i for i in Cluster.objects.all()}
        except django.db.ProgrammingError:
            self.stdout.write(self.style.ERROR('Cluster table does not exist.'))
            sys.exit(1)

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
                cluster["access_token"] = encrypt_value(cluster["access_token"])
                cluster["refresh_token"] = encrypt_value(cluster["refresh_token"])
                cluster["client_secret"] = encrypt_value(cluster["client_secret"])
                self.stdout.write(self.style.NOTICE('Adding cluster: address={}'.format(cluster.get("address"))))
                try:
                    new_cluster = ClusterSettings(**cluster)
                except pydantic.ValidationError as ex:
                    self.stdout.write(self.style.ERROR('Error reading new cluster: {}'.format(ex)))
                    transaction.set_rollback(True)
                    error = True
                    break

                db_cluster = db_clusters.pop(new_cluster.address, None)
                cluster_data = new_cluster.model_dump()
                sync_schedules = cluster_data.pop("sync_schedules", [])
                new_cluster = Cluster(**cluster_data)

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
                # Sync schedule name should be unique per cluster.
                names = [s["name"] for s in sync_schedules]
                duplicates = set([n for n in names if names.count(n) > 1])

                if len(duplicates) > 0:
                    self.stdout.write(self.style.ERROR(f"The sync schedule name must be unique. {", ".join(duplicates)}"))
                    transaction.set_rollback(True)
                    error = True
                    break

                db_schedules = {s.name: s for s in SyncScheduleModel.objects.filter(cluster=new_cluster)}

                for sync_schedule in sync_schedules:
                    errors = validate_rrule(sync_schedule["rrule"])
                    if errors and len(errors) > 0:
                        for error in errors:
                            self.stdout.write(self.style.ERROR(f"{error} - {sync_schedule["name"]}."))
                        transaction.set_rollback(True)
                        error = True
                        break

                    try:
                        rrulestr(sync_schedule["rrule"])
                    except Exception as ex:
                        self.stdout.write(self.style.ERROR(f"Not valid rule for schedule {sync_schedule["name"]} {format(ex)}."))
                        transaction.set_rollback(True)
                        error = True
                        break
                    db_schedule = db_schedules.pop(sync_schedule["name"], None)
                    if db_schedule is None:
                        SyncScheduleModel.objects.create(
                            cluster=new_cluster,
                            name=sync_schedule["name"],
                            rrule=sync_schedule["rrule"],
                            enabled=sync_schedule["enabled"],
                        )
                    else:
                        db_schedule.name = sync_schedule["name"]
                        db_schedule.rrule = sync_schedule["rrule"]
                        db_schedule.enabled = sync_schedule["enabled"]
                        db_schedule.save()

                if error:
                    break

                for key, _db_schedule in db_schedules.items():
                    _db_schedule.delete()

            if not error:
                for key, value in db_clusters.items():
                    value.delete()
        if error:
            sys.exit(1)
        self.stdout.write(self.style.SUCCESS('Successfully set up AAP clusters'))
        if not keep_file:
            self.stdout.write(self.style.NOTICE(f'Removing file {path}'))
            try:
                os.remove(path)
            except Exception as ex:
                self.stdout.write(self.style.ERROR(f'Error removing file {path}: {ex}'))
