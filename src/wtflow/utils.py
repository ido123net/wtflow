import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import TypeVar

T = TypeVar("T")


def import_file(file_path: Path) -> ModuleType:
    module_name = file_path.stem
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    assert spec is not None and spec.loader is not None, f"Cannot find spec for {file_path}"

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module


def import_module(module_path: str) -> ModuleType:
    return importlib.import_module(module_path)
