import argparse
import os
import sys
from pathlib import Path
from typing import Sequence

from wtflow.config import NO_CONFIG, Config
from wtflow.discover import discover_root_nodes
from wtflow.infra.engine import Engine
from wtflow.infra.workflow import Workflow


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wtflow", description="Wtflow - Workflow orchestration tool")

    parser.add_argument(
        "--config",
        "-c",
        help="Path to config file",
        type=Path,
    )
    parser.add_argument(
        "--no-config",
        action="store_true",
        help="Ignore config file",
    )
    parser.add_argument(
        "--file",
        "-f",
        help="Path to workflows directory (default: 'wtfile.py')",
        default="wtfile.py",
        type=Path,
        dest="workflows_path",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute", required=True)

    subparsers.add_parser("list", help="List available workflows")

    run_parser = subparsers.add_parser("run", help="Run a workflow")
    run_parser.add_argument("--workflow", help="Name of the workflow to run", default=None)
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without executing the workflow",
    )

    args = parser.parse_args(argv)

    config = None
    if args.no_config or (os.environ.get(NO_CONFIG, False) and not args.config):
        config = Config()
    elif args.config:
        config = Config.from_ini(args.config)

    if not args.workflows_path.exists():
        print(f"Error: The specified workflows path '{args.workflows_path}' does not exist.", file=sys.stderr)
        return 1

    workflow_dict = discover_root_nodes(args.workflows_path)

    if args.command == "list":
        return _cmd_list(workflow_dict)
    elif args.command == "run":
        return _cmd_run(workflow_dict, args.workflow, config, args.dry_run)
    else:
        raise NotImplementedError


def _cmd_list(workflow_dict: dict[str, Workflow]) -> int:
    if not workflow_dict:
        print("No workflows found.")
        return 0

    print(f"Found {len(workflow_dict)} workflow(s):")
    for name in sorted(workflow_dict):
        print(f"- {name}")

    return 0


def _cmd_run(
    workflow_dict: dict[str, Workflow],
    workflow_name: str | None = None,
    config: Config | None = None,
    dry_run: bool = False,
) -> int:
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    if not workflow_dict:
        print("No workflows found.", file=sys.stderr)
        return 1

    if workflow_name and workflow_name not in workflow_dict:
        print(f"Error: Workflow '{workflow_name}' not found.", file=sys.stderr)
        return 1

    res = 0
    if workflow_name is None:
        wfs = list(workflow_dict.values())
    else:
        wfs = [workflow_dict[workflow_name]]

    for wf in wfs:
        engine = Engine(workflow=wf, config=config, dry_run=dry_run)
        res += engine.run()

    return min(res, 1)


if __name__ == "__main__":
    raise SystemExit(main())
