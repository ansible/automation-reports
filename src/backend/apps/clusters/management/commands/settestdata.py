from datetime import datetime, timezone, timedelta

import pydantic
import yaml
import traceback

from django.core.management import call_command
from django.core.management.base import BaseCommand

from backend.apps.clusters.models import Cluster, ClusterSyncData, ClusterSyncStatus, Organization, JobTemplate, AAPUser, Inventory, ExecutionEnvironment, InstanceGroup, Label, Host, Job, JobLabel, JobHostSummary, JobTypeChoices, JobRunTypeChoices, JobLaunchTypeChoices, JobStatusChoices, Project
from backend.apps.clusters.schemas import ClusterSchema
from django.db import transaction
import random


class Command(BaseCommand):
    help = "Set test data db"
    cluster = None

    def organizations(self, cluster):
        organizations = []
        for i in range(10):
            organizations.append(
                Organization.objects.create(
                    name=f"Organization {i + 1}",
                    description=f"description for organization {i + 1}",
                    external_id=i + 1,
                    cluster=cluster,
                )
            )
        return organizations

    def job_template(self, cluster):
        templates = []
        for i in range(100):
            templates.append(
                JobTemplate.objects.create(
                    name=f"Job template {i + 1}",
                    description=f"description for job_template {i + 1}",
                    external_id=i + 1,
                    cluster=cluster,
                )
            )
        return templates

    def inventory(self, cluster):
        inventory = []
        for i in range(10):
            inventory.append(
                Inventory.objects.create(
                    name=f"Inventory {i + 1}",
                    description=f"description for inventory {i + 1}",
                    external_id=i + 1,
                    cluster=cluster,
                )
            )
        return inventory

    def aapuser(self, cluster):
        users = []
        for i in range(10):
            users.append(
                AAPUser.objects.create(
                    name=f"User {i + 1}",
                    external_id=i + 1,
                    cluster=cluster,
                    type='user'
                )
            )
        return users

    def execution_environment(self, cluster):
        execution_environment = []
        for i in range(10):
            execution_environment.append(
                ExecutionEnvironment.objects.create(
                    name=f"Execution Environment {i + 1}",
                    description=f"description for Execution nvironment {i + 1}",
                    external_id=i + 1,
                    cluster=cluster,
                )
            )
        return execution_environment

    def instance_group(self, cluster):
        instance_group = []
        for i in range(10):
            instance_group.append(
                InstanceGroup.objects.create(
                    name=f"Instance Group {i + 1}",
                    is_container_group=False,
                    external_id=i + 1,
                    cluster=cluster,
                )
            )
        return instance_group

    def label(self, cluster):
        labels = []
        for i in range(10):
            labels.append(
                Label.objects.create(
                    name=f"Label {i + 1}",
                    external_id=i + 1,
                    cluster=cluster,
                )
            )
        return labels

    def host(self, cluster):
        hosts = []
        for i in range(10):
            hosts.append(
                Host.objects.create(
                    name=f"Host {i + 1}",
                    description=f"description for Host {i + 1}",
                    external_id=i + 1,
                    cluster=cluster,
                )
            )
        return hosts

    def projects(self, cluster):
        projects = []
        for i in range(10):
            projects.append(
                Project.objects.create(
                    name=f"Project {i + 1}",
                    description=f"description for Host {i + 1}",
                    external_id=i + 1,
                    scm_type="git",
                    cluster=cluster,
                )
            )
        return projects

    def handle(self, *args, **options):
        call_command("cleardb")
        now = datetime.now(timezone.utc)
        start_date = now.replace(year=now.year - 2, day=1, month=1)
        days = (now - start_date).days

        cluster = Cluster.objects.create(
            protocol="http",
            address="localhost",
            port=8080,
            access_token="test",
            verify_ssl=False
        )
        organizations = self.organizations(cluster)
        templates = self.job_template(cluster)
        aapusers = self.aapuser(cluster)
        inventories = self.inventory(cluster)
        execution_environments = self.execution_environment(cluster)
        instance_groups = self.instance_group(cluster)
        labels = self.label(cluster)
        hosts = self.host(cluster)
        projects = self.projects(cluster)

        for i in range(days):
            created = start_date + timedelta(days=i)
            print(f"Creating job for {created.strftime('%Y-%m-%d')}")
            for j in range(10):
                m = random.randint(0, 59)
                h = random.randint(0, 23)
                job_created = created.replace(hour=h, minute=m)

                template = random.choice(templates)
                organization = random.choice(organizations)
                instance_group = random.choice(instance_groups)
                execution_environment = random.choice(execution_environments)
                inventory = random.choice(inventories)
                launched_by = random.choice(aapusers)
                project = random.choice(projects)
                elapsed = random.randrange(10000, 1000000, 50) / 1000
                job = Job.objects.create(
                    type=JobTypeChoices.JOB,
                    job_type=JobRunTypeChoices.RUN,
                    launch_type=JobLaunchTypeChoices.MANUAL,
                    name=template.name,
                    description=template.description,
                    organization=organization,
                    instance_group=instance_group,
                    execution_environment=execution_environment,
                    inventory=inventory,
                    job_template=template,
                    launched_by=launched_by,
                    status=JobStatusChoices.SUCCESSFUL,
                    started=job_created,
                    finished=job_created,
                    elapsed=elapsed,
                    failed=False,
                    created=job_created,
                    modified=job_created,
                    external_id=i + 1,
                    cluster=cluster,
                    project=project,
                )
                labels_count = random.randrange(0, 9)
                if labels_count > 0:
                    for label_count in range(labels_count):
                        label = random.choice(labels)
                        JobLabel.objects.create(
                            label=label,
                            job=job
                        )

                job_host_summary_count = random.randrange(1, 10)
                count = 0
                for job_hots_count in range(job_host_summary_count):
                    host = random.choice(hosts)
                    JobHostSummary.objects.create(
                        job=job,
                        host=host,
                        host_name=host.name,
                        created=job_created,
                        modified=job_created,
                        ok=1,
                    )
                    count += 1
                job.num_hosts = count
                job.ok_hosts_count = count
                job.save()
