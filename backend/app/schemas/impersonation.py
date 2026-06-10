"""Schemas Pydantic para los endpoints de impersonación."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ImpersonateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID


class ImpersonateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
