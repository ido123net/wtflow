from pathlib import Path

from wtflow.decorator import _ALL_WORKFLOWS
from wtflow.infra.workflow import TreeWorkflow
from wtflow.utils import import_file


def discover_workflows(path: Path | str) -> dict[str, TreeWorkflow]:
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
