from __future__ import annotations

import datetime
import os
import platform
import socket
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from wtflow.infra.nodes import Node
    from wtflow.infra.workflow import Graph


class _SupportTime(Protocol):
    start_time: datetime.datetime | None
    end_time: datetime.datetime | None


T = TypeVar("T", bound=_SupportTime)


@dataclass(frozen=True)
class SystemInfo:
    hostname: str = field(default_factory=socket.gethostname)
    os_name: str = field(default_factory=platform.system)
    os_release: str = field(default_factory=platform.release)
    os_version: str = field(default_factory=platform.version)
    machine: str = field(default_factory=platform.machine)
    cpu_count: int | None = field(default_factory=os.cpu_count)


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)


@dataclass
class RunInfo:
    graph: Graph
    created_at: datetime.datetime = field(default_factory=_utcnow)
    start_time: datetime.datetime | None = None
    end_time: datetime.datetime | None = None
    system_info: SystemInfo = field(default_factory=SystemInfo)


@dataclass
class ExecutionInfo:
    graph: Graph
    node: Node
    start_time: datetime.datetime | None = None
    end_time: datetime.datetime | None = None


@contextmanager
def execute(support_time: T) -> Generator[T]:
    support_time.start_time = _utcnow()
    try:
        yield support_time
    finally:
        support_time.end_time = _utcnow()
