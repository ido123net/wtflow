from textwrap import dedent

import pytest

import wtflow


@pytest.fixture()
def ini_config(tmp_path):
    ini_path = tmp_path / f"{wtflow.__name__}.ini"
    with open(ini_path, "w") as f:
        f.write(
            dedent(
                f"""\
                [database]
                type = orm
                url = sqlite:///{tmp_path}/test.db

                [storage]
                type = local
                path = {tmp_path}/.wtflow_logs

                [run]
                ignore_failure = true
                """
            )
        )
    return ini_path
