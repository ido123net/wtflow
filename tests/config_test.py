from configparser import ConfigParser
from textwrap import dedent

import pytest

from wtflow.config import Config, ConfigError, DatabaseConfig


def test_from_ini(tmp_path, ini_config):
    config = Config.from_ini(ini_path=ini_config)
    assert config.database.url == f"sqlite:///{tmp_path}/test.db"
    assert config.run.ignore_failure is True


def test_from_ini_no_file(tmp_path, ini_config, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = Config.from_ini()
    assert config.database.url == f"sqlite:///{tmp_path}/test.db"
    assert config.run.ignore_failure is True


def test_bad_ini():
    config_parser = ConfigParser()
    config_parser.read_string(
        dedent(
            """\
            [database]
            type = unknown
            url = sqlite:///test.db
            """
        )
    )
    with pytest.raises(ConfigError, match="Unsupported database type: 'unknown'"):
        Config(database=DatabaseConfig.from_config_parser(config_parser))


def test_no_database_section():
    config_parser = ConfigParser()
    config_parser.read_string(
        dedent(
            """\
            [run]
            ignore_failure = true
            """
        )
    )
    config = Config._from_config_parser(config_parser)
    assert config.database is None
    assert config.run.ignore_failure is True


def test_no_type_option():
    config_parser = ConfigParser()
    config_parser.read_string(
        dedent(
            """\
            [database]
            url = sqlite:///test.db
            """
        )
    )
    with pytest.raises(ConfigError, match="database section must have 'type' option"):
        Config(database=DatabaseConfig.from_config_parser(config_parser))
