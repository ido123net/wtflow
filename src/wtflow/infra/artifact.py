from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Artifact:
    name: str
    _id: UUID = field(default_factory=uuid4)
