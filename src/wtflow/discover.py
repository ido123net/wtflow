from pathlib import Path

from wtflow.decorator import _ALL_WORKFLOWS
from wtflow.infra.workflow import Workflow
from wtflow.utils import import_file


def discover_root_nodes(path: Path | str) -> dict[str, Workflow]:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    _ALL_WORKFLOWS.clear()

    if path.is_file() and path.suffix == ".py":
        import_file(path)
    elif path.is_dir():
        for file in path.glob("**/*.py"):
            import_file(file)
    else:
        raise NotImplementedError(f"Unsupported file type: {path}")

    return _ALL_WORKFLOWS
