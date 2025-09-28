import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Type, TypeVar

from wtflow.decorator import _ALL_WORKFLOWS
from wtflow.infra.workflow import Workflow

T = TypeVar("T")


def discover_root_nodes(path: Path | str) -> dict[str, Workflow]:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    _ALL_WORKFLOWS.clear()
    workflows: dict[str, Workflow] = {}

    if path.is_file() and path.suffix == ".py":
        workflows |= _import_file(path)
    elif path.is_dir():
        for file in path.glob("**/*.py"):
            workflows |= _import_file(file)
    else:
        raise NotImplementedError(f"Unsupported file type: {path}")

    return workflows


def get_attr_by_type(module: ModuleType, type_: Type[T]) -> list[T]:
    return [getattr(module, attr) for attr in dir(module) if isinstance(getattr(module, attr), type_)]


def _import_file(file_path: Path) -> dict[str, Workflow]:
    module_name = file_path.stem
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    assert spec is not None and spec.loader is not None, f"Cannot find spec for {file_path}"

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {wf.name: wf for wf in get_attr_by_type(module, Workflow)}
