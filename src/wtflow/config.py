from __future__ import annotations

import logging
import pathlib
import sys
from configparser import ConfigParser, SectionProxy
from dataclasses import dataclass, field

import wtflow
from wtflow.db.service import DBServiceInterface, NoDBService
from wtflow.storage.service import NoStorageService, StorageServiceInterface
from wtflow.utils import import_module

if sys.version_info >= (3, 11):  # pragma: >=3.11 cover
    from typing import Self
else:  # pragma: <3.11 cover
    from typing_extensions import Self

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    @classmethod
    def from_db_section(cls, section: SectionProxy) -> Self:
        raise NotImplementedError

    def create_db_service(self, storage_service: StorageServiceInterface) -> DBServiceInterface:
        return NoDBService(storage_service)

    @classmethod
    def from_config_parser(cls, config: ConfigParser) -> DatabaseConfig:
        if not config.has_section("database"):
            return cls()
        factory_clspath = config.get("database", "factory")
        module_path, class_name = factory_clspath.rsplit(".", 1)
        module = import_module(module_path)
        factory: DatabaseConfig = getattr(module, class_name)
        database_section = config["database"]
        return factory.from_db_section(database_section)


@dataclass
class SQLAlchemyConfig(DatabaseConfig):
    url: str

    @classmethod
    def from_db_section(cls, section: SectionProxy) -> SQLAlchemyConfig:
        url = section.get("url", fallback="sqlite://")
        assert url is not None
        return cls(url=url)

    def create_db_service(self, storage_service: StorageServiceInterface) -> DBServiceInterface:
        from wtflow.db.orm.service import OrmDBService

        return OrmDBService(storage_service, self.url)


@dataclass
class StorageConfig:
    @classmethod
    def from_storage_section(cls, section: SectionProxy) -> Self:
        raise NotImplementedError

    def create_storage_service(self) -> StorageServiceInterface:
        return NoStorageService()

    @classmethod
    def from_config_parser(cls, config: ConfigParser) -> StorageConfig:
        if not config.has_section("storage"):
            return cls()
        factory_clspath = config.get("storage", "factory")
        module_path, class_name = factory_clspath.rsplit(".", 1)
        module = import_module(module_path)
        factory: StorageConfig = getattr(module, class_name)
        storage_section = config["storage"]
        return factory.from_storage_section(storage_section)


@dataclass
class LocalStorageConfig(StorageConfig):
    def __init__(self, base_path: str = ".wtflow_logs") -> None:
        self.base_path = base_path

    @classmethod
    def from_storage_section(cls, section: SectionProxy) -> LocalStorageConfig:
        base_path = section.get("base_path", fallback=".wtflow_logs")
        assert base_path is not None
        return cls(base_path=base_path)

    def create_storage_service(self) -> StorageServiceInterface:
        from wtflow.storage.local.service import LocalStorageService

        return LocalStorageService(base_path=self.base_path)


@dataclass
class RunConfig:
    ignore_failure: bool = False

    @classmethod
    def from_config_parser(cls, config: ConfigParser) -> RunConfig:
        return cls(ignore_failure=config.getboolean("run", "ignore_failure", fallback=cls.ignore_failure))


@dataclass
class Config:
    storage: StorageConfig = field(default_factory=StorageConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
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
            database=DatabaseConfig.from_config_parser(config),
            storage=StorageConfig.from_config_parser(config),
            run=RunConfig.from_config_parser(config),
        )
