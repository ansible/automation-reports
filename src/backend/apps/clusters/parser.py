import decimal
import logging

from django.conf import settings
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

logger = logging.getLogger("automation_dashboard.clusters.parser")


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
        logger.info(f"Initializing DataParser for data_id: {data_id}")
        self.data = None
        self.cluster = None
        self.model = ClusterSyncData.objects.filter(pk=data_id).prefetch_related("cluster").first()
        if self.model:
            logger.debug("ClusterSyncData model found.")
            self.data = ExternalJobSchema(**self.model.data)
            self.cluster = self.model.cluster
        else:
            logger.error(f"No data found for data id: {data_id}")

    @property
    def organization(self) -> Organization | None:
        logger.info("Accessing organization property.")
        external_organization = self.data.summary_fields.organization
        if external_organization:
            logger.debug(f"Parsing organization: {external_organization.name}")
            return Organization.create_or_update(
                cluster=self.cluster,
                external_id=external_organization.id,
                name=external_organization.name,
                description=external_organization.description,
            )
        logger.debug("No external organization found.")
        return None

    @property
    def job_template(self) -> JobTemplate:
        logger.info("Accessing job_template property.")
        external_job_template = self.data.summary_fields.job_template
        job_template = JobTemplate.create_or_update(
            cluster=self.cluster,
            external_id=external_job_template.id if external_job_template else -1,
            name=external_job_template.name if external_job_template else self.data.name,
            description=external_job_template.description if external_job_template else self.data.description,
        )
        job_count = Job.objects.filter(job_template=job_template).count()
        logger.debug(f"Job count for template: {job_count}")
        if job_count == 0:
            logger.info("No jobs exist for this template. Calculating manual execution time.")
            elapsed = self.data.elapsed
            if elapsed is not None:
                manual_execution_time = int(
                    decimal.Decimal(elapsed / 60 * 2).quantize(decimal.Decimal(1), rounding=decimal.ROUND_UP))
                logger.debug(f"Calculated manual execution time: {manual_execution_time}")
                if manual_execution_time < settings.DEFAULT_TIME_TAKEN_TO_MANUALLY_EXECUTE_MINUTES:
                    manual_execution_time = settings.DEFAULT_TIME_TAKEN_TO_MANUALLY_EXECUTE_MINUTES
                if manual_execution_time > 1000000:
                    manual_execution_time = 1000000
                job_template.time_taken_manually_execute_minutes = manual_execution_time
                job_template.save(update_fields=['time_taken_manually_execute_minutes'])
                logger.info("Manual execution time updated for job template.")
        return job_template

    @property
    def launched_by(self) -> AAPUser | None:
        logger.info("Accessing launched_by property.")
        external_launched_by = self.data.launched_by
        if external_launched_by and external_launched_by.id:
            logger.debug(f"Parsing launched_by: {external_launched_by.name}")
            return AAPUser.create_or_update(
                cluster=self.cluster,
                external_id=external_launched_by.id,
                name=external_launched_by.name,
                type=external_launched_by.type,
            )
        logger.debug("No external launched_by found.")
        return None

    @property
    def inventory(self) -> Inventory | None:
        logger.info("Accessing inventory property.")
        external_inventory = self.data.summary_fields.inventory
        if external_inventory:
            logger.debug(f"Parsing inventory: {external_inventory.name}")
            return Inventory.create_or_update(
                cluster=self.cluster,
                external_id=external_inventory.id,
                name=external_inventory.name,
                description=external_inventory.description,
            )
        logger.debug("No external inventory found.")
        return None

    @property
    def execution_environment(self) -> ExecutionEnvironment | None:
        logger.info("Accessing execution_environment property.")
        external_execution_environment = self.data.summary_fields.execution_environment
        if external_execution_environment is not None:
            logger.debug(f"Parsing execution_environment: {external_execution_environment.name}")
            return ExecutionEnvironment.create_or_update(
                cluster=self.cluster,
                external_id=external_execution_environment.id,
                name=external_execution_environment.name,
                description=external_execution_environment.description,
            )
        logger.debug("No external execution_environment found.")
        return None

    @property
    def instance_group(self) -> InstanceGroup | None:
        logger.info("Accessing instance_group property.")
        external_instance_group = self.data.summary_fields.instance_group
        if external_instance_group is not None:
            logger.debug(f"Parsing instance_group: {external_instance_group.name}")
            return InstanceGroup.create_or_update(
                cluster=self.cluster,
                external_id=external_instance_group.id,
                name=external_instance_group.name,
                is_container_group=external_instance_group.is_container_group,
            )
        logger.debug("No external instance_group found.")
        return None

    def get_label(self, external_label: LabelModelSchema) -> Label:
        logger.info(f"Getting label: {external_label.name}")
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
            logger.debug("No external labels found, using empty list.")
            external_labels = LabelsSchema(**{
                "count": 0,
                "results": []
            })
        for label in external_labels.results:
            logger.debug(f"Yielding label: {label.name}")
            yield self.get_label(label)

    @property
    def project(self) -> Project | None:
        logger.info("Accessing project property.")
        external_project = self.data.summary_fields.project
        if external_project is not None:
            logger.debug(f"Parsing project: {external_project.name}")
            return Project.create_or_update(
                cluster=self.cluster,
                external_id=external_project.id,
                name=external_project.name,
                description=external_project.description,
                scm_type=external_project.scm_type,
            )
        logger.debug("No external project found.")
        return None

    def get_host(self, host: NameDescriptionModelSchema | None, host_name: str) -> Host:
        logger.info(f"Getting host: {host_name}")
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
            logger.debug("No external host summaries found, using empty list.")
            external_host_summaries = []
        for host_summary in external_host_summaries:
            logger.debug(f"Processing host summary for host: {host_summary.host_name}")
            summary_fields = host_summary.summary_fields
            host = self.get_host(summary_fields.host, host_summary.host_name)
            data = host_summary.model_dump()
            data.pop("summary_fields")
            data["host"] = host
            yield data

    @property
    def job(self):
        logger.info("Accessing job property.")
        data = self.data.model_dump()
        for key in ["summary_fields", "launched_by", "execution_environment", "host_summaries"]:
            data.pop(key, None)
        logger.debug(f"Job data: {data}")
        return data

    def parse(self):
        logger.info("Starting parse process.")
        if self.data is None:
            logger.warning("No data to parse.")
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
                logger.info("No job found, creating new job.")
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
                logger.info("Job already exists, updating job.")
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
            logger.debug(f"Existing job labels: {list(db_job_labels.keys())}")

            for label in self.labels:
                db_label = db_job_labels.pop(label.id, None)
                if db_label is None:
                    logger.info(f"Creating new job label for label id: {label.id}")
                    JobLabel.objects.create(job=job, label=label)

            for key, value in db_job_labels.items():
                logger.info(f"Deleting old job label with label id: {key}")
                value.delete()

            logger.info("Deleting job host summaries.")
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

            logger.info("Processing job summary counts.")
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

            logger.info("Updating job with summary counts.")
            job.save()

            logger.info("Finished processing and deleting record.")
            self.model.delete()
