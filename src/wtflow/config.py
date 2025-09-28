from __future__ import annotations

import logging
import pathlib
import sys
from abc import ABC, abstractmethod
from configparser import ConfigParser, NoOptionError, SectionProxy
from dataclasses import dataclass, field
from enum import Enum

if sys.version_info >= (3, 11):  # pragma: >=3.11 cover
    from typing import Self
else:  # pragma: <3.11 cover
    from typing_extensions import Self

import wtflow
from wtflow.db.service import DBServiceInterface

logger = logging.getLogger(__name__)


class DBType(str, Enum):
    ORM = "orm"


class ConfigError(Exception):
    pass


@dataclass
class DatabaseConfig(ABC):
    @classmethod
    @abstractmethod
    def from_db_section(cls, section: SectionProxy) -> Self: ...

    @abstractmethod
    def create_db_service(self) -> DBServiceInterface: ...

    @classmethod
    def from_config_parser(cls, config: ConfigParser) -> DatabaseConfig | None:
        try:
            type_ = config.get("database", "type")
            db_type = DBType(type_)
        except NoOptionError:
            raise ConfigError("database section must have 'type' option") from None
        except ValueError:
            raise ConfigError(f"Unsupported database type: {type_!r}") from None

        if db_type is DBType.ORM:
            database_section = config["database"]
            return SQLAlchemyConfig.from_db_section(database_section)
        else:
            raise NotImplementedError


@dataclass
class SQLAlchemyConfig(DatabaseConfig):
    url: str

    @classmethod
    def from_db_section(cls, section: SectionProxy) -> SQLAlchemyConfig:
        url = section.get("url", fallback="sqlite://")
        assert url is not None
        return cls(url=url)

    def create_db_service(self) -> DBServiceInterface:
        from wtflow.db.orm.service import OrmDBService

        return OrmDBService(self.url)


@dataclass
class RunConfig:
    ignore_failure: bool = False

    @classmethod
    def from_config_parser(cls, config: ConfigParser) -> RunConfig:
        return cls(ignore_failure=config.getboolean("run", "ignore_failure", fallback=cls.ignore_failure))


@dataclass
class Config:
    database: DatabaseConfig | None = None
    run: RunConfig = field(default_factory=RunConfig)

    @classmethod
    def from_ini(cls, ini_path: str | pathlib.Path | None = None) -> Config:
        ini_path = ini_path or pathlib.Path(f"{wtflow.__name__}.ini")

        config = ConfigParser()
        config.read(ini_path)
        return cls._from_config_parser(config)

    @classmethod
    def _from_config_parser(cls, config: ConfigParser) -> Config:
        return cls(
            database=DatabaseConfig.from_config_parser(config) if config.has_section("database") else None,
            run=RunConfig.from_config_parser(config),
        )
