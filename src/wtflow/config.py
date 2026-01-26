from __future__ import annotations

import logging
import os
import pathlib
import sys
from configparser import ConfigParser, SectionProxy

from pydantic import BaseModel

import wtflow
from wtflow.services.db.service import DBServiceInterface, NoDBService
from wtflow.services.storage.service import NoStorageService, StorageServiceInterface
from wtflow.utils import load_clspath

if sys.version_info >= (3, 11):  # pragma: >=3.11 cover
    from typing import Self
else:  # pragma: <3.11 cover
    from typing_extensions import Self

logger = logging.getLogger(__name__)

NO_CONFIG = "WTFLOW_NO_CONFIG"


class DatabaseConfig(BaseModel):
    @classmethod
    def from_db_section(cls, section: SectionProxy) -> Self:
        raise NotImplementedError

    def create_db_service(self) -> DBServiceInterface:
        return NoDBService()

    @classmethod
    def from_config_parser(cls, config: ConfigParser) -> DatabaseConfig:
        if not config.has_section("database"):
            return cls()
        factory_clspath = config.get("database", "factory")
        factory: DatabaseConfig = load_clspath(factory_clspath)
        database_section = config["database"]
        return factory.from_db_section(database_section)


class Sqlite3Config(DatabaseConfig):
    database_path: str

    @classmethod
    def from_db_section(cls, section: SectionProxy) -> Sqlite3Config:
        database_path = section.get("database_path", fallback=".wtflow.db")
        assert database_path is not None
        return cls(database_path=database_path)

    def create_db_service(self) -> DBServiceInterface:
        from wtflow.services.db.sqlite.service import Sqlite3DBService

        return Sqlite3DBService(self.database_path)


class StorageConfig(BaseModel):
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
        factory: StorageConfig = load_clspath(factory_clspath)
        storage_section = config["storage"]
        return factory.from_storage_section(storage_section)


class LocalStorageConfig(StorageConfig):
    base_path: pathlib.Path

    @classmethod
    def from_storage_section(cls, section: SectionProxy) -> LocalStorageConfig:
        base_path = section.get("base_path", fallback=".wtflow_logs")
        assert base_path is not None
        return cls(base_path=pathlib.Path(base_path))

    def create_storage_service(self) -> StorageServiceInterface:
        from wtflow.services.storage.local.service import LocalStorageService

        return LocalStorageService(base_path=self.base_path)


class RunConfig(BaseModel):
    ignore_failure: bool = False

    @classmethod
    def from_config_parser(cls, config: ConfigParser) -> RunConfig:
        return cls(ignore_failure=config.getboolean("run", "ignore_failure", fallback=False))


class Config(BaseModel):
    storage: StorageConfig = StorageConfig()
    database: DatabaseConfig = DatabaseConfig()
    run: RunConfig = RunConfig()

    @classmethod
    def from_ini(cls, ini_path: str | pathlib.Path | None = None) -> Config:
        if os.environ.get(NO_CONFIG, False) and not ini_path:
            return cls()

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
