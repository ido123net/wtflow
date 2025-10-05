import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Type, TypeVar

T = TypeVar("T")


def get_attr_by_type(module: ModuleType, type_: Type[T]) -> list[T]:
    return [getattr(module, attr) for attr in dir(module) if isinstance(getattr(module, attr), type_)]


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
