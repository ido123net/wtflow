# What The Flow (wtflow)

Wtflow is a powerful asynchronous workflow runner that orchestrates complex tasks and dependencies with ease.

## Features

- Define workflows with a tree-like structure of nodes
- Execute shell commands or Python functions
- Run nodes in parallel or sequentially
- Automatic capture of stdout/stderr streams
- Configurable storage of execution artifacts
- Database tracking of workflow execution

## Installation

```bash
# Install from PyPI
pip install wtflow

# Or install from source
git clone https://github.com/ido123net/wtflow.git
cd wtflow
uv sync
```

## Quick Start

```python
# main.py
import sys

import wtflow


def func():
    print("STDOUT")
    print("STDERR", file=sys.stderr)


def func_process_stream(artifact: wtflow.Artifact):
    print(f"processing {artifact.name}: {artifact.data}")


def main():
    n1 = wtflow.Node(
        name="Node 1",
        executable=wtflow.PyFunc(func=func),
    )
    n2 = wtflow.Node(
        name="Node 2",
        executable=wtflow.PyFunc(
            func=func_process_stream,
            args=(n1.stdout_artifact,),
        ),
    )
    n3 = wtflow.Node(
        name="Node 3",
        executable=wtflow.PyFunc(
            func=func_process_stream,
            args=(n1.stderr_artifact,),
        ),
    )

    wf = wtflow.Workflow(
        name="WTFLOW Example",
        root=wtflow.Node(
            name="Root Node",
            executable=wtflow.Command("echo Starting workflow"),
            children=[n1, n2, n3],
        ),
    )
    engine = wtflow.Engine(wf)
    return engine.run()


if __name__ == "__main__":
    raise SystemExit(main())
```

The output will be:
```bash
$ python main.py
Starting workflow
STDOUT
STDERR
processing stdout: b'STDOUT\n'
processing stderr: b'STDERR\n'
```

## Configuration

Wtflow can be configured using environment variables or an INI file.

### Environment Variables

Configuration options are organized into these categories:

**Database:**
- `WTFLOW_DB_URL`: Database URL for storing workflow execution data

**Storage:**
- `WTFLOW_ARTIFACTS_DIR`: Directory path for storing execution artifacts

**Run:**
- `WTFLOW_IGNORE_FAILURE`: Continue workflow execution despite node failures (accepts: 0, 1, true, false)

### INI File Configuration

You can also configure wtflow using an INI file:

```ini
[database]
url = sqlite:///my-workflows.db

[storage]
artifacts_dir = /path/to/artifacts

[run]
ignore_failure = false
```

Load the configuration in your code:

```python
config = wtflow.Config.from_ini("/path/to/config.ini")
engine = wtflow.Engine(workflow, config=config)
```

## Architecture

Wtflow is built around these key concepts:

- **Workflow**: The top-level container representing a complete pipeline
- **Node**: A single executable unit that may have children
- **Executable**: The actual task to run (Command or PyFunc)
- **Artifact**: Output or result data from node execution
- **Engine**: Orchestrates workflow execution

## Development

### Setup development environment

```bash
# Clone the repository
git clone https://github.com/ido123net/wtflow.git
cd wtflow

# Install dependencies
uv sync

# Setup pre-commit hooks
pre-commit install
```

### Run tests

```bash
pytest
```

## License

MIT License - See [LICENSE](LICENSE) file for details.
