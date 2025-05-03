from textwrap import dedent

import pytest

from wtflow.config import Config, RunConfig


def test_invalid_ignore_failure(monkeypatch):
    monkeypatch.setenv("WTFLOW_IGNORE_FAILURE", "invalid_value")

    with pytest.raises(ValueError, match="WTFLOW_IGNORE_FAILURE must be one of: 0, 1, true, false"):
        Config(run=RunConfig.from_env())


def test_from_ini(tmp_path):
    ini_path = tmp_path / "test_config.ini"
    with open(ini_path, "w") as f:
        f.write(
            dedent(
                """\
                [database]
                url = sqlite:///test.db

                [storage]
                artifacts_dir = /path/to/artifacts

                [run]
                ignore_failure = true
                max_fail = 5
                """
            )
        )
    config = Config.from_ini(ini_path)
    assert config.db.url == "sqlite:///test.db"
    assert str(config.storage.artifacts_dir) == "/path/to/artifacts"
    assert config.run.ignore_failure is True
    assert config.run.max_fail == 5
