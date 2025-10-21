import decimal
from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class SyncSchedule(BaseModel):
    name: str
    rrule: str
    enabled: bool | None = True


class ClusterSettings(FrozenModel):
    protocol: str
    address: str
    port: int
    access_token: bytes
    verify_ssl: bool = True
    sync_schedules: List[SyncSchedule] | None = []


class ClusterSchema(ClusterSettings):
    aap_version: Literal["AAP 2.5", "AAP 2.4"] | None = None
    api_url: str
    base_url: str


class DateRangeSchema(BaseModel):
    start: datetime
    end: datetime

    @property
    def iso_format(self) -> dict[str, str]:
        return {
            "start": self.start.isoformat().replace('+00:00', 'Z') if self.start else None,
            "end": self.end.isoformat().replace('+00:00', 'Z') if self.end else None,
        }


class QueryParams(BaseModel):
    date_range: DateRangeSchema | None = None
    organization: List[int] | None = None
    job_template: List[int] | None = None
    label: List[int] | None = None
    project: List[int] | None = None
    cluster: List[int] | None = None


class RelatedLinks(BaseModel):
    successful_jobs: str | None = ""
    failed_jobs: str | None = ""


class NameDescriptionModelSchema(FrozenModel):
    id: int
    name: str
    description: str | None = ""


class InstanceGroup(FrozenModel):
    id: int
    name: str
    is_container_group: bool | None = False


class LabelModelSchema(FrozenModel):
    id: int
    name: str


class LabelsSchema(FrozenModel):
    count: int
    results: List[LabelModelSchema]


class ProjectSchema(FrozenModel):
    id: int
    name: str
    scm_type: str | None = ""
    description: str | None = ""


class SummaryFields(FrozenModel):
    organization: NameDescriptionModelSchema | None = None
    job_template: NameDescriptionModelSchema | None = None
    inventory: NameDescriptionModelSchema | None = None
    execution_environment: NameDescriptionModelSchema | None = None
    instance_group: InstanceGroup | None = None
    labels: LabelsSchema
    project: ProjectSchema | None = None


class LaunchedBy(FrozenModel):
    id: int | None = None
    name: str | None = None
    type: str | None = None


class HostSummarySummaryFieldsSchema(FrozenModel):
    host: NameDescriptionModelSchema | None = None


class HostSummarySchema(FrozenModel):
    summary_fields: HostSummarySummaryFieldsSchema | None = None
    host_name: str | None = ""
    changed: int
    dark: int
    failures: int
    ok: int
    processed: int
    skipped: int
    failed: bool
    ignored: int
    rescued: int
    created: datetime
    modified: datetime


class ExternalJobSchema(FrozenModel):
    model_config = ConfigDict(frozen=True)
    id: int
    name: str
    description: str
    launched_by: LaunchedBy
    summary_fields: SummaryFields
    host_summaries: List[HostSummarySchema]
    started: datetime | None = None
    finished: datetime | None = None
    elapsed: decimal.Decimal | None = None
    failed: bool
    status: Literal["new", "pending", "waiting", "running", "successful", "failed", "error", "canceled"]
    job_type: Literal["run", "check", "scan"]
    type: Literal["job", "Playbook Run"]
    launch_type: Literal["manual", "relaunch", "callback", "scheduled", "dependency", "workflow", "webhook", "sync", "scm"]
    created: datetime
    modified: datetime


class ReportDataValue(FrozenModel):
    value: float | int | None = 0


class TopUsers(FrozenModel):
    user_id: int
    user_name: str
    count: int


class TopProjects(FrozenModel):
    project_id: int
    project_name: str
    count: int


class ReportData(FrozenModel):
    total_number_of_unique_hosts: ReportDataValue | None = ReportDataValue(value=0)
    total_number_of_successful_jobs: ReportDataValue | None = ReportDataValue(value=0)
    total_number_of_failed_jobs: ReportDataValue | None = ReportDataValue(value=0)
    total_number_of_job_runs: ReportDataValue | None = ReportDataValue(value=0)
    total_number_of_host_job_runs: ReportDataValue | None = ReportDataValue(value=0)
    total_hours_of_automation: ReportDataValue | None = ReportDataValue(value=0)
    cost_of_automated_execution: ReportDataValue | None = ReportDataValue(value=0)
    cost_of_manual_automation: ReportDataValue | None = ReportDataValue(value=0)
    total_saving: ReportDataValue | None = ReportDataValue(value=0)
    total_time_saving: ReportDataValue | None = ReportDataValue(value=0)
    users: List[TopUsers] | None = []
    projects: List[TopProjects] | None = []


class ChartItem(BaseModel):
    x: datetime | None = None
    y: int | None = None


class ChartData(BaseModel):
    items: List[ChartItem] | None = []
    range: str | None = None


class ChartsData(FrozenModel):
    host_chart: ChartData | None = ChartData()
    job_chart: ChartData | None = ChartData()
