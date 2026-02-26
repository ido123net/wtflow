from __future__ import annotations

import pathlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from wtflow.services.db.db_service import DBServiceInterface, NoDBService
from wtflow.services.storage.storage_service import NoStorageService, StorageServiceInterface


class DatabaseConfig(ABC):
    @abstractmethod
    def create_db_service(self) -> DBServiceInterface:
        return NotImplemented


class NoDatabaseConfig(DatabaseConfig):
    def create_db_service(self) -> DBServiceInterface:
        return NoDBService()


@dataclass
class Sqlite3Config(DatabaseConfig):
    database_path: str

    def create_db_service(self) -> DBServiceInterface:
        from wtflow.services.db.sqlite.sqlite_db_service import Sqlite3DBService

        return Sqlite3DBService(self.database_path)


class StorageConfig(ABC):
    @abstractmethod
    def create_storage_service(self) -> StorageServiceInterface:
        return NotImplemented


class NoStorageConfig(StorageConfig):
    def create_storage_service(self) -> StorageServiceInterface:
        return NoStorageService()


@dataclass
class LocalStorageConfig(StorageConfig):
    base_path: pathlib.Path

    def create_storage_service(self) -> StorageServiceInterface:
        from wtflow.services.storage.local.local_storage_service import LocalStorageService

        return LocalStorageService(base_path=self.base_path)


@dataclass
class Config:
    database: DatabaseConfig = field(default_factory=NoDatabaseConfig)
    storage: StorageConfig = field(default_factory=NoStorageConfig)
