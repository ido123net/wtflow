import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Sequence

from wtflow.config import Config
from wtflow.discover import discover_workflows
from wtflow.infra.engine import Engine
from wtflow.infra.workflow import Workflow


def main(argv: Sequence[str] | None = None) -> int:
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    parser = argparse.ArgumentParser(prog="wtflow", description="Wtflow - Workflow orchestration tool")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute", required=True)

    list_parser = subparsers.add_parser("list", help="List available workflows")
    run_parser = subparsers.add_parser("run", help="Run a workflow")

    for subparser in [list_parser, run_parser]:
        subparser.add_argument(
            "workflows_path",
            help="Path to workflows directory (default: 'wtfile.py')",
            default="wtfile.py",
            type=Path,
            nargs="?",
        )

    run_parser.add_argument("--workflow", help="Name of the workflow to run", default=None)
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without executing the workflow",
    )

    args = parser.parse_args(argv)

    config = Config()
    wf_path: Path = args.workflows_path
    if not wf_path.exists():
        print(f"Error: The specified workflows path '{args.workflows_path}' does not exist.", file=sys.stderr)
        return 1

    workflow_dict = discover_workflows(args.workflows_path)

    if args.command == "list":
        return _cmd_list(workflow_dict)
    elif args.command == "run":
        return asyncio.run(_cmd_run(workflow_dict, args.workflow, config, args.dry_run))
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


async def _cmd_run(
    workflow_dict: dict[str, Workflow],
    workflow_name: str | None = None,
    config: Config | None = None,
    dry_run: bool = False,
) -> int:
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

    if dry_run:
        print(json.dumps([workflow.model_dump(exclude_defaults=True) for workflow in wfs], indent=2))
        return 0

    for wf in wfs:
        engine = Engine(config=config)
        res += await engine.run_workflow(workflow=wf)

    return min(res, 1)


if __name__ == "__main__":
    raise SystemExit(main())
