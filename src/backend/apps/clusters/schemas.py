from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClusterSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    protocol: str
    host: str
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
