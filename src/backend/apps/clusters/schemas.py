import decimal
from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class ClusterSchema(FrozenModel):
    model_config = ConfigDict(frozen=True)

    protocol: str
    address: str
    port: int
    access_token: str
    verify_ssl: bool = True


class DateRangeSchema(BaseModel):
    start: datetime
    end: datetime
    prev_start: datetime
    prev_end: datetime

    @property
    def iso_format(self) -> dict[str, str]:
        return {
            "start": self.start.isoformat().replace('+00:00', 'Z') if self.start else None,
            "end": self.end.isoformat().replace('+00:00', 'Z') if self.end else None,
            "prev_start": self.prev_start.isoformat().replace('+00:00', 'Z') if self.prev_start else None,
            "prev_end": self.prev_end.isoformat().replace('+00:00', 'Z') if self.prev_end else None,
        }


class NameDescriptionModelSchema(FrozenModel):
    id: int
    name: str
    description: str


class InstanceGroup(FrozenModel):
    id: int
    name: str
    is_container_group: bool


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


class SummaryFields(FrozenModel):
    organization: NameDescriptionModelSchema | None
    job_template: NameDescriptionModelSchema | None
    inventory: NameDescriptionModelSchema | None
    execution_environment: NameDescriptionModelSchema | None
    instance_group: InstanceGroup | None
    labels: LabelsSchema
    project: ProjectSchema | None


class LaunchedBy(FrozenModel):
    id: int
    name: str
    type: str


class HostSummarySummaryFieldsSchema(FrozenModel):
    host: NameDescriptionModelSchema | None


class HostSummarySchema(FrozenModel):
    summary_fields: HostSummarySummaryFieldsSchema
    host_name: str
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
    started: datetime
    finished: datetime | None
    elapsed: decimal.Decimal | None
    failed: bool
    status: Literal["new", "pending", "waiting", "running", "successful", "failed", "error", "canceled"]
    job_type: Literal["run", "check", "scan"]
    type: Literal["job", "Playbook Run"]
    launch_type: Literal["manual", "relaunch", "callback", "scheduled", "dependency", "workflow", "webhook", "sync", "scm"]
