import argparse
import asyncio
import logging
import pathlib
from typing import Sequence

from wtflow.engine import Engine
from wtflow.parser import parse_yaml

logger = logging.getLogger(__name__)


async def run(engine: Engine) -> int:
    result = await engine.run()
    logger.info(
        f"workflow result: {result}\n"
        f"{
            engine.workflow.root.model_dump_json(
                indent=2,
                exclude_none=True,
                exclude_defaults=True,
            )
        }"
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wtflow", description="Tool to run workflows")

    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity")

    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a workflow")
    run_parser.add_argument("file", type=pathlib.Path, help="Path to the workflow file")

    status_parser = subparsers.add_parser("status", help="Get the status of a workflow")
    status_parser.add_argument("id", help="ID of the workflow")

    args = parser.parse_args(argv)

    if args.verbose == 1:
        level = logging.INFO
    elif args.verbose >= 2:
        level = logging.DEBUG

    if args.verbose:
        logging.basicConfig(level=level, format="%(taskName)s: %(message)s")

    if args.command == "run":
        workflow = parse_yaml(args.file)
        engine = Engine(workflow)
        return asyncio.run(run(engine))
    else:
        raise NotImplementedError(f"Command {args.command} not implemented")


if __name__ == "__main__":
    raise SystemExit(main())
