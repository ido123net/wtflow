import pytest

from wtflow.config import Config, RunConfig


def test_invalid_ignore_failure(monkeypatch):
    monkeypatch.setenv("WTFLOW_IGNORE_FAILURE", "invalid_value")

    with pytest.raises(ValueError, match="WTFLOW_IGNORE_FAILURE must be one of: 0, 1, true, false"):
        Config(run=RunConfig.from_env())


def test_from_ini(tmp_path, ini_config):
    config = Config.from_ini(ini_path=ini_config)
    assert config.db.url == f"sqlite:///{tmp_path}/test.db"
    assert config.run.ignore_failure is True
