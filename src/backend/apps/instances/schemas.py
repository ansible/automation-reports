from pydantic import BaseModel, ConfigDict


class InstanceSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    protocol: str
    host: str
    port: int
    access_token: str
    verify_ssl: bool = True

