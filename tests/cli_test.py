import pathlib

import pytest
from wtflow.cli import main


@pytest.mark.parametrize("verbosity", [0, 1, 2])
def test_main(file_path: pathlib.Path, verbosity: int):
    args = [f"-{'v' * verbosity}"] if verbosity else []
    assert main(args + ["run", str(file_path)]) == 0


def test_main_not_implemented():
    with pytest.raises(NotImplementedError):
        main(["status", "id"])
