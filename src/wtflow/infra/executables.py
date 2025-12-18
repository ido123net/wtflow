from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Command:
    timeout: float | None = field(default=None, kw_only=True)
    cmd: str
