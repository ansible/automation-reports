import logging

from django.db import transaction

from backend.apps.clusters.models import (
    ClusterSyncData,
    Organization,
    JobTemplate,
    AAPUser,
    Inventory,
    ExecutionEnvironment,
    InstanceGroup,
    Label,
    Job,
    JobLabel,
    Host,
    JobHostSummary, Project)
from backend.apps.clusters.schemas import (
    ExternalJobSchema,
    NameDescriptionModelSchema,
    LabelModelSchema,
    LabelsSchema)

logger = logging.getLogger("automation-dashboard")


class DataParser:

    def __init__(self, data_id):
        self.data = None
        self.cluster = None
        self.model = ClusterSyncData.objects.filter(pk=data_id).prefetch_related("cluster").first()
        if self.model:
            self.data = ExternalJobSchema(**self.model.data)
            self.cluster = self.model.cluster
        else:
            logger.error("No data found for data id: {}".format(data_id))

    @property
    def organization(self) -> Organization | None:
        logger.info("Getting organization for cluster: {}".format(self.cluster))
        external_organization = self.data.summary_fields.organization
        data = external_organization.model_dump()
        external_id = data.pop("id")
        if external_organization:
            organization = (Organization.objects.
                            filter(external_id=external_id, cluster=self.cluster).first())
            if organization is None:
                logger.info("No organization found, let's create new")
                organization = (Organization.objects.
                                create(external_id=external_id, cluster=self.cluster, **data))
                logger.info("New organization created.")
            else:
                logger.info("Organization already exists, updating.")
                organization.name = data.pop("name")
                organization.description = data.pop("description", "")
                organization.save()
                logger.info("Organization updated.")
            return organization
        return None

    @property
    def job_template(self) -> JobTemplate:
        logger.info("Getting job template for cluster: {}".format(self.cluster))
        external_job_template = self.data.summary_fields.job_template
        template_name = external_job_template.name if external_job_template else self.data.name
        template_description = external_job_template.description if external_job_template else self.data.description
        external_id = external_job_template.id if external_job_template else -1

        if external_id > 0:
            job_template = JobTemplate.objects.filter(cluster=self.cluster, external_id=external_id).first()
        else:
            job_template = JobTemplate.objects.filter(cluster=self.cluster, name=template_name).first()
        if job_template is None:
            logger.info("No job template found, let's create new")
            job_template = JobTemplate.objects.create(cluster=self.cluster, external_id=external_id, name=template_name, description=template_description)
            logger.info("New job template created.")
        else:
            logger.info("Job template already exists, updating.")
            job_template.description = template_description
            job_template.name = template_name
            job_template.external_id = external_id if external_id > 0 else job_template.external_id
            job_template.save()
            logger.info("Job template updated.")
        job_template.save()

        return job_template

    @property
    def launched_by(self) -> AAPUser | None:
        logger.info("Getting AAP user for cluster: {}".format(self.cluster))
        external_launched_by = self.data.launched_by
        if external_launched_by is not None:
            data = external_launched_by.model_dump()
            external_id = data.pop("id")
            launched_by = AAPUser.objects.filter(cluster=self.cluster, external_id=external_id).first()
            if launched_by is None:
                logger.info("No AAP user, let's create new")
                launched_by = AAPUser.objects.create(cluster=self.cluster, external_id=external_id, **data)
                logger.info("New AAP user created.")
            else:
                logger.info("AAP user already exists, updating.")
                launched_by.name = data.pop("name")
                launched_by.type = data.pop("type")
                launched_by.save()
                logger.info("AAP user updated.")
            return launched_by
        return None

    @property
    def inventory(self):
        logger.info("Getting inventory for cluster: {}".format(self.cluster))
        external_inventory = self.data.summary_fields.inventory
        if external_inventory is not None:
            data = external_inventory.model_dump()
            external_id = data.pop("id")
            inventory = Inventory.objects.filter(cluster=self.cluster, external_id=external_id).first()
            if inventory is None:
                logger.info("No inventory found, let's create new")
                inventory = Inventory.objects.create(cluster=self.cluster, external_id=external_id, **data)
                logger.info("New inventory created.")
            else:
                logger.info("Inventory already exists, updating.")
                inventory.name = data.pop("name")
                inventory.description = data.pop("description", "")
                inventory.save()
                logger.info("Inventory updated.")
            return inventory
        return None

    @property
    def execution_environment(self) -> ExecutionEnvironment | None:
        logger.info("Getting execution environment for cluster: {}".format(self.cluster))
        external_execution_environment = self.data.summary_fields.execution_environment
        if external_execution_environment is not None:
            data = external_execution_environment.model_dump()
            external_id = data.pop("id")

            execution_environment = (ExecutionEnvironment.objects
                                     .filter(
                cluster=self.cluster,
                external_id=external_id).first())
            if execution_environment is None:
                logger.info("No execution environment found, let's create new")
                execution_environment = ExecutionEnvironment.objects.create(cluster=self.cluster, external_id=external_id, **data)
                logger.info("New execution environment created.")
            else:
                logger.info("Execution environment already exists, updating.")
                execution_environment.name = data.pop("name")
                execution_environment.description = data.pop("description", "")
                execution_environment.save()
                logger.info("Execution environment updated.")
            return execution_environment
        return None

    @property
    def instance_group(self):
        logger.info("Getting instance group for cluster: {}".format(self.cluster))
        external_instance_group = self.data.summary_fields.instance_group
        if external_instance_group is not None:
            data = external_instance_group.model_dump()
            external_id = data.pop("id")
            instance_group = InstanceGroup.objects.filter(cluster=self.cluster, external_id=external_id).first()
            if instance_group is None:
                logger.info("No instance group found, let's create new")
                instance_group = InstanceGroup.objects.create(cluster=self.cluster, external_id=external_id, **data)
                logger.info("New instance group created.")
            else:
                logger.info("Instance group already exists, updating.")
                instance_group.name = data.pop("name")
                instance_group.is_container_group = data.pop("is_container_group", False)
                instance_group.save()
                logger.info("New instance group created.")
            return instance_group
        return None

    def get_label(self, external_label: LabelModelSchema) -> Label:
        name = external_label.name
        external_id = external_label.id
        label = Label.objects.filter(cluster=self.cluster, external_id=external_id).first()
        if label is None:
            logger.info("No label found, let's create new")
            label = Label.objects.create(cluster=self.cluster, external_id=external_id, name=name)
            logger.info("New label created.")
        else:
            logger.info("Label already exists, updating.")
            label.name = name
            label.save()
            logger.info("Label updated.")
        return label

    @property
    def labels(self):
        logger.info("Getting labels.")
        external_labels = self.data.summary_fields.labels
        if external_labels is None or external_labels.count == 0:
            external_labels = LabelsSchema(**{
                "count": 0,
                "results": []
            })
        for label in external_labels.results:
            yield self.get_label(label)

    @property
    def project(self):
        logger.info("Getting project for cluster: {}".format(self.cluster))
        external_project = self.data.summary_fields.project
        if external_project is not None:
            data = external_project.model_dump()
            external_id = data.pop("id")
            project = Project.objects.filter(cluster=self.cluster, external_id=external_id).first()
            if project is None:
                logger.info("No project found, let's create new")
                project = Project.objects.create(cluster=self.cluster, external_id=external_id, **data)
                logger.info("New project created.")
            else:
                logger.info("Project already exists, updating.")
                project.name = data.pop("name")
                project.description = data.pop("description", "")
                project.scm_type = data.pop("scm_type", "")
                project.save()
                logger.info("Project updated.")
            return project
        return None

    def get_host(self, host: NameDescriptionModelSchema | None, host_name: str) -> Host:
        name = host.name if host else host_name
        description = host.description if host else ""
        external_id = host.id if host else -1

        if host is not None:
            db_host = Host.objects.filter(cluster=self.cluster, external_id=host.id).first()
        else:
            db_host = Host.objects.filter(cluster=self.cluster, name=host_name).first()

        if db_host is None:
            logger.info("No host found, let's create new")
            db_host = Host.objects.create(cluster=self.cluster, external_id=external_id, name=name, description=description)
            logger.info("New host created.")
        else:
            logger.info("Host already exists, updating.")
            db_host.name = name
            db_host.description = description
            db_host.external_id = external_id if external_id > 0 else db_host.external_id
            db_host.save()
            logger.info("Host updated.")

        return db_host

    @property
    def host_summaries(self):
        logger.info("Getting host summaries.")
        external_host_summaries = self.data.host_summaries
        if not external_host_summaries:
            external_host_summaries = []
        for host_summary in external_host_summaries:
            summary_fields = host_summary.summary_fields
            host = self.get_host(summary_fields.host, host_summary.host_name)
            data = host_summary.model_dump()
            data.pop("summary_fields")
            data["host"] = host
            yield data

    @property
    def job(self):
        data = self.data.model_dump()
        for key in ["summary_fields", "launched_by", "execution_environment", "host_summaries"]:
            data.pop(key, None)
        return data

    def parse(self):
        if self.data is None:
            return

        organization = self.organization
        job_template = self.job_template
        launched_by = self.launched_by
        inventory = self.inventory
        execution_environment = self.execution_environment
        instance_group = self.instance_group
        project = self.project
        job_data = self.job
        external_id = job_data.pop("id")

        with transaction.atomic():
            job = Job.objects.filter(cluster=self.cluster, external_id=external_id).first()
            if job is None:
                logger.info("No job found, let's create new")
                job = Job.objects.create(
                    cluster=self.cluster,
                    external_id=external_id,
                    organization=organization,
                    instance_group=instance_group,
                    execution_environment=execution_environment,
                    inventory=inventory,
                    job_template=job_template,
                    launched_by=launched_by,
                    project=project,
                    **job_data
                )
            else:
                logger.info("Job already exists, updating.")
                job.type = job_data.pop("type")
                job.job_type = job_data.pop("job_type")
                job.launch_type = job_data.pop("launch_type")
                job.name = job_data.pop("name")
                job.description = job_data.pop("description")
                job.organization = organization
                job.instance_group = instance_group
                job.execute_environment = execution_environment
                job.instance_group = instance_group
                job.job_template = job_template
                job.launched_by = launched_by
                job.project = project
                job.created = job_data.pop("created")
                job.modified = job_data.pop("modified")
                job.save()
                logger.info("Job updated.")

            db_job_labels = {label.label_id: label for label in JobLabel.objects.filter(job=job)}

            for label in self.labels:
                db_label = db_job_labels.pop(label.id, None)
                if db_label is None:
                    logger.info("Creating new job label.")
                    JobLabel.objects.create(job=job, label=label)

            for key, value in db_job_labels.items():
                logger.info("Deleting old job label(s).")
                value.delete()

            logger.info("Deleting job host summary(s).")
            JobHostSummary.objects.filter(job=job).delete()

            num_hosts = 0
            changed_hosts_count = 0
            dark_hosts_count = 0
            failures_hosts_count = 0
            ok_hosts_count = 0
            processed_hosts_count = 0
            skipped_hosts_count = 0
            failed_hosts_count = 0
            ignored_hosts_count = 0
            rescued_hosts_count = 0

            for host_summary in self.host_summaries:
                logger.info("Processing host summary.")
                num_hosts += 1
                changed_hosts_count += host_summary.get("changed", 0)
                dark_hosts_count += host_summary.get("dark", 0)
                failures_hosts_count += host_summary.get("failures", 0)
                ok_hosts_count += host_summary.get("ok", 0)
                processed_hosts_count += host_summary.get("processed", 0)
                skipped_hosts_count += host_summary.get("skipped", 0)
                failed_hosts_count += 1 if host_summary.get("failed", True) is False else 0
                ignored_hosts_count += host_summary.get("ignored", 0)
                rescued_hosts_count += host_summary.get("rescued", 0)
                logger.info("Creating new host summary.")
                JobHostSummary.objects.create(job=job, **host_summary)

            logger.info("Processing summaries.")
            job.num_hosts = num_hosts
            job.changed_hosts_count = changed_hosts_count
            job.dark_hosts_count = dark_hosts_count
            job.failures_hosts_count = failures_hosts_count
            job.ok_hosts_count = ok_hosts_count
            job.processed_hosts_count = processed_hosts_count
            job.skipped_hosts_count = skipped_hosts_count
            job.failed_hosts_count = failed_hosts_count
            job.ignored_hosts_count = ignored_hosts_count
            job.rescued_hosts_count = rescued_hosts_count

            logger.info("Updating job with summaries.")
            job.save()

            logger.info("Finished processing and deleting record.")
            self.model.delete()
