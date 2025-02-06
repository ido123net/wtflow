import os

from yaml import safe_load

from wtflow.workflow import Workflow


def parse_yaml(file_path: os.PathLike) -> Workflow:
    with open(file_path, "r") as file:
        obj = safe_load(file)
    return Workflow.model_validate(obj)
