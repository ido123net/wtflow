from dataclasses import dataclass


@dataclass
class Artifact:
    name: str
    uri: str | None = None
