import importlib.util
import sys
from pathlib import Path

from wtflow.decorator import ROOT_NODES
from wtflow.infra.nodes import Node


def discover_root_nodes(path: Path | str) -> dict[str, Node]:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    # Clear existing workflows to avoid duplicates
    ROOT_NODES.clear()

    if path.is_file() and path.suffix == ".py":
        _import_file(path)
    elif path.is_dir():
        for file in path.glob("**/*.py"):
            _import_file(file)
    else:
        raise NotImplementedError(f"Unsupported file type: {path}")

    return ROOT_NODES


def _import_file(file_path: Path) -> None:
    module_name = file_path.stem
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    assert spec is not None and spec.loader is not None, f"Cannot find spec for {file_path}"

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
