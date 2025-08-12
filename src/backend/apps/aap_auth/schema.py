from backend.apps.clusters.schemas import FrozenModel
from pydantic import Field
from typing import Literal

class AAPAuthSettings(FrozenModel):
    name: str = Field(..., min_length=3)
    protocol: Literal['http', 'https']
    url: str = Field(..., min_length=1)
    user_data_endpoint: str = Field(..., min_length=1)
    check_ssl: bool
    client_id: str = Field(..., min_length=1)
    client_secret: str = Field(..., min_length=1)

class AAPToken(FrozenModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
