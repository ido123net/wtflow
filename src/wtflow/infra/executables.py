from __future__ import annotations

from pydantic import BaseModel, Field


class Command(BaseModel):
    timeout: float | None = Field(default=None, kw_only=True)
    cmd: str
