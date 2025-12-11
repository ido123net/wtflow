from dataclasses import dataclass
from typing import Any


@dataclass
class Artifact:
    name: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name}
