from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AuthCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def email_must_be_simple_and_normalized(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("email must be valid")
        return normalized


class CurrentUser(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    email: str
    created_at: datetime
    updated_at: datetime
