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

    @property
    def iso_format(self) -> dict[str, str]:
        return {
            "start": self.start.isoformat().replace('+00:00', 'Z') if self.start else None,
            "end": self.end.isoformat().replace('+00:00', 'Z') if self.end else None,
        }


class NameDescriptionModelSchema(FrozenModel):
    id: int
    name: str
    description: str | None = ""


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
    organization: NameDescriptionModelSchema | None = None
    job_template: NameDescriptionModelSchema | None = None
    inventory: NameDescriptionModelSchema | None = None
    execution_environment: NameDescriptionModelSchema | None = None
    instance_group: InstanceGroup | None = None
    labels: LabelsSchema
    project: ProjectSchema | None = None


class LaunchedBy(FrozenModel):
    id: int
    name: str
    type: str


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
    started: datetime
    finished: datetime | None = None
    elapsed: decimal.Decimal | None = None
    failed: bool
    status: Literal["new", "pending", "waiting", "running", "successful", "failed", "error", "canceled"]
    job_type: Literal["run", "check", "scan"]
    type: Literal["job", "Playbook Run"]
    launch_type: Literal["manual", "relaunch", "callback", "scheduled", "dependency", "workflow", "webhook", "sync", "scm"]
