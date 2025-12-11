import argparse
import os
import sys
from typing import Sequence

import typer

from wtflow.utils import load_clspath


def main(argv: Sequence[str] | None = None) -> int:
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    parser = argparse.ArgumentParser(prog="wtflow", description="Run python function (using `Typer`)")
    parser.add_argument("funcpath", help="Python path to the function to run (e.g. `packageA.moduleB.func`)")
    args, func_args = parser.parse_known_args(argv)
    return _run_func(args.funcpath, func_args)


def _run_func(funcpath: str, args: list[str]) -> int:
    func = load_clspath(funcpath)
    app = typer.Typer(add_completion=False)
    app.command()(func)
    try:
        return app(args, prog_name=funcpath)
    except SystemExit as ex:
        assert isinstance(ex.code, int)
        return ex.code


if __name__ == "__main__":
    raise SystemExit(main())
