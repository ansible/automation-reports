import calendar
import datetime
import decimal
import logging
import os

import pytz
from dateutil.relativedelta import relativedelta
from django.db import models

from backend.apps.clusters.schemas import DateRangeSchema
from backend.django_config import settings

manual_time = int(os.environ.get("DEFAULT_TIME_TAKEN_TO_MANUALLY_EXECUTE_MINUTES", "60"))
automation_time = int(os.environ.get("DEFAULT_TIME_TAKEN_TO_CREATE_AUTOMATION_MINUTES", "60"))

logger = logging.getLogger('automation_dashboard.models')


class CreatUpdateModel(models.Model):
    internal_created = models.DateTimeField(auto_now_add=True, blank=True, editable=False)
    internal_modified = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        abstract = True


class ClusterVersionChoices(models.TextChoices):
    AAP25 = "AAP 2.5", "AAP 2.5"
    AAP24 = "AAP 2.4", "AAP 2.4"


class Cluster(CreatUpdateModel):
    protocol = models.CharField(max_length=10)
    address = models.CharField(max_length=255)
    port = models.IntegerField()
    access_token = models.TextField()
    verify_ssl = models.BooleanField(default=True)
    aap_version = models.CharField(max_length=15, choices=ClusterVersionChoices.choices, default=ClusterVersionChoices.AAP24)

    def __str__(self):
        return f'{self.protocol}://{self.address}:{self.port}'

    @property
    def base_url(self):
        return f'{self.protocol}://{self.address}:{self.port}'

    @property
    def api_url(self):
        if self.aap_version == ClusterVersionChoices.AAP25:
            return f'/api/controller/v2'
        elif self.aap_version == ClusterVersionChoices.AAP24:
            return f'/api/v2'
        else:
            raise NotImplementedError

    @property
    def gui_base_url(self):
        if self.aap_version == ClusterVersionChoices.AAP25:
            return f'{self.base_url}/execution/'
        elif self.aap_version == ClusterVersionChoices.AAP24:
            return f'{self.base_url}/#/'
        else:
            raise NotImplementedError

    @property
    def cache_timeout_blocked(self):
        from backend.apps.scheduler.models import SyncJob, JobTypeChoices as SyncJobTypeChoices
        # Only one sync per cluster
        if SyncJob.objects.filter(
                cluster=self,
                status__in=[JobStatusChoices.PENDING, JobStatusChoices.WAITING, JobStatusChoices.RUNNING],
                type=SyncJobTypeChoices.SYNC_JOBS
        ).count() > 0:
            logger.error(
                "Sync Job template %s could not be started because there are more than %s other jobs from that template waiting to run"
                % (self, 1)
            )
            return True
        return False

    def create_sync_job(self, **kwargs):
        from backend.apps.scheduler.models import SyncJob, JobTypeChoices as SyncJobTypeChoices
        return SyncJob.objects.create(cluster=self, type=SyncJobTypeChoices.SYNC_JOBS, **kwargs)


class DateRangeChoices(models.TextChoices):
    LAST_YEAR = "last_year", "Past year"
    LAST_6_MONTH = "last_6_month", "Past 6 months"
    LAST_3_MONTH = "last_3_month", "Past 3 months"
    LAST_MONTH = "last_month", "Past month"
    YEAR_TO_DATE = "year_to_date", "Year to date"
    QUARTER_TO_DATE = "quarter_to_date", "Quarter to date"
    MONTH_TO_DATE = "month_to_date", "Month to date"
    LAST_3_YEARS = "last_3_years", "Past 3 years"
    LAST_2_YEARS = "last_2_years", "Past 2 years"
    CUSTOM = "custom", "Custom"

    @classmethod
    def get_date_range(cls, choice, start: str = None, end: str = None) -> DateRangeSchema:
        now = datetime.datetime.now(pytz.utc)
        match choice:
            case cls.LAST_YEAR:
                start_date = now.replace(year=now.year - 1, month=1, day=1)
                end_date = now.replace(year=now.year - 1, month=12, day=31)

            case cls.LAST_3_YEARS:
                start_date = now.replace(year=now.year - 3, month=1, day=1)
                end_date = now.replace(year=now.year - 1, month=12, day=31)

            case cls.LAST_2_YEARS:
                start_date = now.replace(year=now.year - 2, month=1, day=1)
                end_date = now.replace(year=now.year - 1, month=12, day=31)

            case cls.LAST_3_MONTH:
                end_date = now - relativedelta(months=1)
                num_days = calendar.monthrange(end_date.year, end_date.month)[1]
                end_date = end_date.replace(day=num_days)
                start_date = now - relativedelta(months=3)
                start_date = start_date.replace(day=1)

            case cls.LAST_6_MONTH:
                end_date = now - relativedelta(months=1)
                num_days = calendar.monthrange(end_date.year, end_date.month)[1]
                end_date = end_date.replace(day=num_days)
                start_date = now - relativedelta(months=6)
                start_date = start_date.replace(day=1)

            case cls.LAST_MONTH:
                end_date = now - relativedelta(months=1)
                num_days = calendar.monthrange(end_date.year, end_date.month)[1]
                end_date = end_date.replace(day=num_days)
                start_date = end_date.replace(day=1)

            case cls.YEAR_TO_DATE:
                end_date = now
                start_date = now.replace(month=1, day=1)

            case cls.MONTH_TO_DATE:
                end_date = now
                start_date = now.replace(day=1)

            case cls.QUARTER_TO_DATE:
                end_date = now
                quarter = (now.month - 1) // 3 + 1
                quarter_start_month = 3 * quarter - 2
                start_date = now.replace(day=1, month=int(quarter_start_month))

            case cls.CUSTOM:
                try:
                    start_date = datetime.datetime.fromisoformat(start)
                except (ValueError, TypeError):
                    start_date = now

                try:
                    end_date = datetime.datetime.fromisoformat(end)
                except (ValueError, TypeError):
                    end_date = now

            case _:
                raise NotImplementedError
        start = datetime.datetime.combine(start_date, datetime.time.min, pytz.utc)
        end = datetime.datetime.combine(end_date, datetime.time.max, pytz.utc)

        return DateRangeSchema(**{
            'start': start,
            'end': end,
        })


class JobStatusChoices(models.TextChoices):
    NEW = "new", "New"
    PENDING = "pending", "Pending"
    WAITING = "waiting", "Waiting"
    RUNNING = "running", "Running"
    SUCCESSFUL = "successful", "Successful"
    FAILED = "failed", "Failed"
    ERROR = "error", "Error"
    CANCELED = "canceled", "Canceled"


class JobTypeChoices(models.TextChoices):
    JOB = "job", "Job"
    PLAYBOOK_RUN = "Playbook Run", "Playbook Run"


class JobLaunchTypeChoices(models.TextChoices):
    MANUAL = "manual", "Manual"
    RELAUNCH = "relaunch", "Relaunch"
    CALLBACK = "callback", "Callback"
    SCHEDULED = "scheduled", "Scheduled"
    DEPENDENCY = "dependency", "Dependency"
    WORKFLOW = "workflow", "Workflow"
    WEBHOOK = "webhook", "Webhook"
    SYNC = "sync", "Sync"
    SCM = "scm", "SCM Update"


class JobRunTypeChoices(models.TextChoices):
    RUN = "run", "Run"
    CHECK = "check", "Check"
    SCAN = "scan", "Scan"


class ClusterSyncData(CreatUpdateModel):
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE, related_name='sync_data')
    data = models.JSONField()

    def __str__(self):
        return f'{self.cluster.protocol}://{self.cluster.address}:{self.cluster.port} - {self.pk}'

    @property
    def cache_timeout_blocked(self):
        from backend.apps.scheduler.models import SyncJob, JobTypeChoices as SyncJobTypeChoices
        # Max limit for data parser
        limit = settings.SCHEDULE_MAX_DATA_PARSE_JOBS
        if SyncJob.objects.filter(
                cluster=self.cluster,
                status__in=[JobStatusChoices.PENDING, JobStatusChoices.WAITING, JobStatusChoices.RUNNING],
                type=SyncJobTypeChoices.PARSE_JOB_DATA).count() >= limit:
            logger.error(
                "Parse job data %s could not be started because there are more than %s other jobs from that template waiting to run"
                % (self, limit)
            )
            return True
        return False

    def save(self, *args, **kwargs):
        from backend.apps.scheduler.models import SyncJob, JobTypeChoices as SyncJobTypeChoices
        super(ClusterSyncData, self).save(*args, **kwargs)

        ### This code creates a new `SynJob` instance with specific fields set.
        ### It is used to trigger a background job related to parsing data for a cluster job.
        SyncJob.objects.create(
            name='Data parser',
            cluster=self.cluster,
            cluster_sync_data=self,
            type=SyncJobTypeChoices.PARSE_JOB_DATA,
            launch_type=JobLaunchTypeChoices.WORKFLOW,
        )


class ClusterSyncStatus(CreatUpdateModel):
    cluster = models.OneToOneField(Cluster, on_delete=models.CASCADE, related_name='status')
    last_job_finished_date = models.DateTimeField()

    def __str__(self):
        return f'{self.cluster.protocol}://{self.cluster.address}:{self.cluster.port}'


class BaseModel(CreatUpdateModel):
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)
    external_id = models.IntegerField()

    class Meta:
        abstract = True
        index_together = (
            ('cluster', 'external_id'),
        )


class NameDescriptionModel(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Organization(NameDescriptionModel):
    class Meta:
        abstract = False


class JobTemplate(NameDescriptionModel):
    time_taken_manually_execute_minutes = models.IntegerField(default=manual_time)
    time_taken_create_automation_minutes = models.IntegerField(default=automation_time)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, related_name='job_templates')

    class Meta:
        abstract = False


class AAPUser(BaseModel):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.type}:{self.name}"


class Inventory(NameDescriptionModel):
    class Meta:
        abstract = False


class ExecutionEnvironment(NameDescriptionModel):
    class Meta:
        abstract = False


class InstanceGroup(BaseModel):
    name = models.CharField(max_length=255)
    is_container_group = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Label(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Host(NameDescriptionModel):
    class Meta:
        abstract = False


class Project(NameDescriptionModel):
    scm_type = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        abstract = False


class Job(BaseModel):
    type = models.CharField(choices=JobTypeChoices.choices, default=JobTypeChoices.JOB, max_length=20)
    job_type = models.CharField(choices=JobRunTypeChoices.choices, default=JobTypeChoices.JOB, max_length=20)
    launch_type = models.CharField(choices=JobLaunchTypeChoices.choices, default=JobLaunchTypeChoices.MANUAL, max_length=20)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, related_name='jobs')
    instance_group = models.ForeignKey(InstanceGroup, on_delete=models.CASCADE, null=True, related_name='jobs')
    execution_environment = models.ForeignKey(ExecutionEnvironment, on_delete=models.CASCADE, null=True, related_name='jobs')
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, null=True, related_name='jobs')
    job_template = models.ForeignKey(JobTemplate, on_delete=models.CASCADE, null=True, related_name='jobs')
    launched_by = models.ForeignKey(AAPUser, on_delete=models.CASCADE, null=True, related_name='jobs')
    status = models.CharField(choices=JobStatusChoices.choices, default=JobStatusChoices.SUCCESSFUL, max_length=25)
    started = models.DateTimeField()
    finished = models.DateTimeField(null=True, blank=True)
    elapsed = models.DecimalField(max_digits=15, decimal_places=3, default=decimal.Decimal(0))
    failed = models.BooleanField(default=False)
    created = models.DateTimeField(null=True, blank=True)
    modified = models.DateTimeField(null=True, blank=True)
    num_hosts = models.IntegerField(default=0)
    changed_hosts_count = models.IntegerField(default=0)
    dark_hosts_count = models.IntegerField(default=0)
    failures_hosts_count = models.IntegerField(default=0)
    ok_hosts_count = models.IntegerField(default=0)
    processed_hosts_count = models.IntegerField(default=0)
    skipped_hosts_count = models.IntegerField(default=0)
    failed_hosts_count = models.IntegerField(default=0)
    ignored_hosts_count = models.IntegerField(default=0)
    rescued_hosts_count = models.IntegerField(default=0)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, related_name='jobs')

    class Meta:
        abstract = False
        indexes = [
            models.Index(fields=['status', 'finished']),
        ]
        index_together = ('cluster', 'job_template'),


class JobLabel(CreatUpdateModel):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='labels')
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='jobs')

    def __str__(self):
        return f'{self.label.name}: {self.job.name}'


class JobHostSummary(CreatUpdateModel):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='host_summary')
    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name="jobs", null=True)
    host_name = models.CharField(max_length=255, null=True, blank=True)
    changed = models.IntegerField(default=0)
    dark = models.IntegerField(default=0)
    failures = models.IntegerField(default=0)
    ok = models.IntegerField(default=0)
    processed = models.IntegerField(default=0)
    skipped = models.IntegerField(default=0)
    failed = models.BooleanField(default=False)
    ignored = models.IntegerField(default=0)
    rescued = models.IntegerField(default=0)
    created = models.DateTimeField()
    modified = models.DateTimeField()

    def __str__(self):
        return f'{self.job.name} - {self.host.name}'


class CostsChoices(models.TextChoices):
    MANUAL = "manual", "Manual"
    AUTOMATED = "automated", "Automated"


class Costs(CreatUpdateModel):
    value = models.DecimalField(max_digits=15, decimal_places=2, default=decimal.Decimal(0))
    type = models.CharField(choices=CostsChoices.choices, unique=True, max_length=20)

    def __str__(self):
        return f'{self.type}: {self.value}'
