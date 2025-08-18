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
    JobHostSummary,
    Project)
from backend.apps.clusters.schemas import (
    ExternalJobSchema,
    NameDescriptionModelSchema,
    LabelModelSchema,
    LabelsSchema)

logger = logging.getLogger("automation-dashboard")


class DataParser:
    """
   DataParser is responsible for extracting and transforming external job data
   from a ClusterSyncData instance. It provides properties and methods to
   retrieve or create related model instances (such as Organization, JobTemplate,
   Inventory, etc.) and to parse and persist job and host summary information
   into the database. The class ensures data consistency and handles updates
   or creation of related objects as needed.
   """

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
        external_organization = self.data.summary_fields.organization
        if external_organization:
            return Organization.create_or_update(
                cluster=self.cluster,
                external_id=external_organization.id,
                name=external_organization.name,
                description=external_organization.description,
            )
        return None

    @property
    def job_template(self) -> JobTemplate:
        external_job_template = self.data.summary_fields.job_template
        return JobTemplate.create_or_update(
            cluster=self.cluster,
            external_id=external_job_template.id if external_job_template else -1,
            name=external_job_template.name if external_job_template else self.data.name,
            description=external_job_template.description if external_job_template else self.data.description,
        )

    @property
    def launched_by(self) -> AAPUser | None:
        external_launched_by = self.data.launched_by
        if external_launched_by and external_launched_by.id:
            return AAPUser.create_or_update(
                cluster=self.cluster,
                external_id=external_launched_by.id,
                name=external_launched_by.name,
                type=external_launched_by.type,
            )
        return None

    @property
    def inventory(self) -> Inventory | None:
        external_inventory = self.data.summary_fields.inventory
        if external_inventory:
            return Inventory.create_or_update(
                cluster=self.cluster,
                external_id=external_inventory.id,
                name=external_inventory.name,
                description=external_inventory.description,
            )
        return None

    @property
    def execution_environment(self) -> ExecutionEnvironment | None:
        external_execution_environment = self.data.summary_fields.execution_environment
        if external_execution_environment is not None:
            return ExecutionEnvironment.create_or_update(
                cluster=self.cluster,
                external_id=external_execution_environment.id,
                name=external_execution_environment.name,
                description=external_execution_environment.description,
            )
        return None

    @property
    def instance_group(self) -> InstanceGroup | None:
        external_instance_group = self.data.summary_fields.instance_group
        if external_instance_group is not None:
            return InstanceGroup.create_or_update(
                cluster=self.cluster,
                external_id=external_instance_group.id,
                name=external_instance_group.name,
                is_container_group=external_instance_group.is_container_group,
            )
        return None

    def get_label(self, external_label: LabelModelSchema) -> Label:
        return Label.create_or_update(
            cluster=self.cluster,
            external_id=external_label.id,
            name=external_label.name,
        )

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
    def project(self) -> Project | None:
        external_project = self.data.summary_fields.project
        if external_project is not None:
            return Project.create_or_update(
                cluster=self.cluster,
                external_id=external_project.id,
                name=external_project.name,
                description=external_project.description,
                scm_type=external_project.scm_type,
            )
        return None

    def get_host(self, host: NameDescriptionModelSchema | None, host_name: str) -> Host:
        name = host.name if host else host_name
        description = host.description if host else ""
        external_id = host.id if host else -1

        return Host.create_or_update(
            cluster=self.cluster,
            external_id=external_id,
            name=name,
            description=description,
        )

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
                failed_hosts_count += 1 if host_summary.get("failed", True) is True else 0
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
