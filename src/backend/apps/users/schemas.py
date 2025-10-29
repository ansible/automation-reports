from typing import List

from pydantic import BaseModel

class UserSchema(BaseModel):
    username: str
    email: str
    first_name: str | None = None
    last_name: str | None = None
    is_superuser: bool | None = False
    is_platform_auditor: bool | None = False
    is_system_auditor: bool | None = False


class UserResponseSchema(BaseModel):
    count: int
    results: List[UserSchema]
