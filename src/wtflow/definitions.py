from enum import StrEnum, auto

from pydantic import BaseModel, Field


class Outcome(StrEnum):
    INITIAL = auto()
    SUCCESS = auto()
    FAILURE = auto()
    TIMEOUT = auto()
    STOPPED = auto()


class Result(BaseModel):
    retcode: int | None = None
    stdout: bytes = Field(b"", exclude=True)
    stderr: bytes = Field(b"", exclude=True)
