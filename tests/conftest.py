from textwrap import dedent

import pytest


@pytest.fixture()
def ini_config(tmp_path):
    ini_path = tmp_path / "test_config.ini"
    with open(ini_path, "w") as f:
        f.write(
            dedent(
                f"""\
                [database]
                url = sqlite:///{tmp_path}/test.db

                [storage]
                artifacts_dir = {tmp_path}/artifacts

                [run]
                ignore_failure = true
                """
            )
        )
    return ini_path
