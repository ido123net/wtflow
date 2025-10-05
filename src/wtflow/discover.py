from pathlib import Path

import wtflow
from wtflow.decorator import _ALL_WORKFLOWS
from wtflow.infra.workflow import Workflow
from wtflow.utils import get_attr_by_type, import_file


def _import_workflows_from_file(path: Path) -> dict[str, Workflow]:
    module = import_file(path)
    return {wf.name: wf for wf in get_attr_by_type(module, wtflow.Workflow)}


def discover_root_nodes(path: Path | str) -> dict[str, Workflow]:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    _ALL_WORKFLOWS.clear()
    workflows: dict[str, Workflow] = {}

    if path.is_file() and path.suffix == ".py":
        workflows |= _import_workflows_from_file(path)
    elif path.is_dir():
        for file in path.glob("**/*.py"):
            workflows |= _import_workflows_from_file(file)
    else:
        raise NotImplementedError(f"Unsupported file type: {path}")

    return workflows
