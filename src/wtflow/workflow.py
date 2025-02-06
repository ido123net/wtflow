from pydantic import BaseModel
from wtflow.nodes import Node


class Workflow(BaseModel):
    name: str
    root: Node
