from configparser import ConfigParser, NoOptionError
from textwrap import dedent

import pytest

from wtflow.config import Config, DatabaseConfig, Sqlite3Config


def test_from_ini(tmp_path, ini_config):
    config = Config.from_ini(ini_path=ini_config)
    assert isinstance(config.database, Sqlite3Config)
    assert config.database.database_path == f"{tmp_path}/test.db"


def test_from_ini_no_file(tmp_path, ini_config, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = Config.from_ini()
    assert isinstance(config.database, Sqlite3Config)
    assert config.database.database_path == f"{tmp_path}/test.db"


def test_bad_ini_not_clspath():
    config_parser = ConfigParser()
    config_parser.read_string(
        dedent(
            """\
            [database]
            factory = unknown
            database_path = test.db
            """
        )
    )
    with pytest.raises(ValueError, match="not enough values to unpack"):
        Config(database=DatabaseConfig.from_config_parser(config_parser))


def test_bad_ini_clspath_not_exists():
    config_parser = ConfigParser()
    config_parser.read_string(
        dedent(
            """\
            [database]
            factory = unknown.UnknownClass
            database_path = test.db
            """
        )
    )
    with pytest.raises(ModuleNotFoundError, match="No module named 'unknown'"):
        Config(database=DatabaseConfig.from_config_parser(config_parser))


def test_no_database_section():
    config_parser = ConfigParser()
    config = Config._from_config_parser(config_parser)
    assert config.database == DatabaseConfig()


def test_no_type_option():
    config_parser = ConfigParser()
    config_parser.read_string(
        dedent(
            """\
            [database]
            database_path = test.db
            """
        )
    )
    with pytest.raises(NoOptionError, match="No option 'factory' in section: 'database'"):
        Config(database=DatabaseConfig.from_config_parser(config_parser))
